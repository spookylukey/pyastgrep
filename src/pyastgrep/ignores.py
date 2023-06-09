from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Generator, Union, overload

from pathspec import GitIgnoreSpec, PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern


class DirectoryPathSpec:
    """
    PathSpec object for a specific directory.
    """

    # We have to keep track of the location of a .gitignore file, as well as
    # its contents, in order to correctly handle patterns like:
    #
    #   /foo
    #
    # which should match `foo` in the same directory as the .gitignore file,
    # but not in other directories.
    def __init__(self, location: Path, pathspec: PathSpec):
        self.location = location
        self.pathspec = pathspec

    def match_file(self, path: Path) -> bool:
        try:
            relative = path.relative_to(self.location)
        except ValueError:
            # Could happen if `path` is not relative to (i.e. below) self.location.
            # Possible for symlinks perhaps? How do we interpret the
            # .gitignore file correctly if we don't know where the file
            # is relative to it?
            # Rather than crash, we ignore the file
            return False
        else:
            return self.pathspec.match_file(relative)


PathSpecLike = Union[PathSpec, DirectoryPathSpec]


@overload
def add_negative_dir_pattern(pathspec: PathSpec, directory: Path) -> PathSpec:
    pass


@overload
def add_negative_dir_pattern(pathspec: DirectoryPathSpec, directory: Path) -> DirectoryPathSpec:
    pass


def add_negative_dir_pattern(pathspec: PathSpec | DirectoryPathSpec, directory: Path) -> PathSpec | DirectoryPathSpec:
    if isinstance(pathspec, DirectoryPathSpec):
        return DirectoryPathSpec(pathspec.location, add_negative_dir_pattern(pathspec.pathspec, directory))
    return pathspec.__class__(list(pathspec.patterns) + [GitWildMatchPattern(f"!{directory}/")])


class DirWalker:
    """
    Walks a directory recursively, returning files that match a glob,
    while automatically respecting dot-ignore files
    """

    def __init__(
        self,
        *,
        glob: str,
        pathspecs: list[PathSpecLike] | None = None,
        init_global_pathspecs: bool = True,
        start_directory: Path | None = None,
        working_dir: Path | None = None,
        absolute_base: bool = False,
    ):
        # DirWalker is immutable outside __init__
        self.glob: str = glob
        if pathspecs is None:
            pathspecs = []
        if init_global_pathspecs:
            global_gitignore = get_global_gitignore()
            if global_gitignore and global_gitignore.exists():
                pathspecs.append(pathspec_for_gitignore(global_gitignore, is_global_gitignore=True))
            # POSIX hidden files:
            pathspecs.append(PathSpec([GitWildMatchPattern(".*")]))
        self.pathspecs: list[PathSpecLike] = pathspecs
        self.start_directory: Path | None = start_directory
        self.working_dir = working_dir
        self.absolute_base: bool = absolute_base

    def for_dir(self, directory: Path, working_dir: Path) -> DirWalker:
        """
        Return a new DirWalker, customised for the directory.
        """
        # Here we keep the already loaded global gitignore, and add any
        # more needed, up to and including the current directory.
        base_directory = directory.resolve()
        pathspecs = self.pathspecs + [
            pathspec_for_gitignore(ignorepath) for ignorepath in find_gitignore_files(base_directory, recurse_up=True)
        ]
        # We also need to add a negative override to ensure that paths specified
        # directly are not ignored.
        if directory != Path("."):
            # TODO this doesn't work in all cases, e.g. if an exclude is specified
            # in a subdirectory `.gitignore` which matches the passed in directory.
            pathspecs = [add_negative_dir_pattern(pathspec, directory) for pathspec in pathspecs]

        return DirWalker(
            glob=self.glob,
            pathspecs=pathspecs,
            init_global_pathspecs=False,
            start_directory=base_directory,
            working_dir=working_dir,
            absolute_base=directory.is_absolute(),
        )

    def for_subdir(self, directory: Path) -> DirWalker:
        """
        Return a new DirWalker, customised for the subdirectory of
        the directory the parent current walker is for.
        """
        # This is distinct from `for_dir`, so that we can re-use the work
        # that has already been done in checking parent dirs for .gitignore files,
        # and just check the new current dir.
        if self.start_directory is None:
            raise AssertionError("Must use `for_dir` before `for_subdir`")
        extra_pathspecs: list[PathSpecLike] = [
            pathspec_for_gitignore(ignorepath) for ignorepath in find_gitignore_files(directory, recurse_up=False)
        ]

        return DirWalker(
            glob=self.glob,
            pathspecs=self.pathspecs + extra_pathspecs,
            init_global_pathspecs=False,
            start_directory=directory,
            working_dir=self.working_dir,
            absolute_base=self.absolute_base,
        )

    def walk(self) -> Generator[Path, None, None]:
        if self.start_directory is None or self.working_dir is None:
            raise AssertionError("Must use `for_dir` before `walk`")
        for filepath in self.start_directory.glob(self.glob):
            if filepath.is_symlink():
                # Follow default behaviour of ripgrep, and avoid issues with
                # `resolve().relative_to(working_dir)
                continue
            if filepath.is_file():
                if any(pathspec.match_file(filepath) for pathspec in self.pathspecs):
                    continue
                if self.absolute_base:
                    yield filepath
                else:
                    yield filepath.resolve().relative_to(self.working_dir)
        for subdir in self.start_directory.iterdir():
            if subdir.is_symlink():
                continue
            if subdir.is_dir():
                if any(pathspec.match_file(subdir) for pathspec in self.pathspecs):
                    continue
                yield from self.for_subdir(subdir).walk()


def pathspec_for_gitignore(gitignore_file: Path, is_global_gitignore: bool = False) -> PathSpec | DirectoryPathSpec:
    with open(gitignore_file) as fp:
        spec = GitIgnoreSpec.from_lines(fp)
        if is_global_gitignore:
            return spec
        else:
            return DirectoryPathSpec(gitignore_file.parent, spec)


def find_gitignore_files(starting_path: Path, *, recurse_up: bool = True) -> list[Path]:
    """
    For a given working dir, returns a list of .gitignore files
    that apply to it.
    """
    files = []

    # Not 100% sure this is correct or what ripgrep does,
    # but it probably covers the most common setups
    current_path = starting_path.resolve()
    while True:
        candidate = current_path / ".gitignore"
        if candidate.exists():
            files.append(candidate)
        if not recurse_up:
            break
        if (current_path / ".git").exists():
            # Found the root git repo, stop searching
            break
        parent = current_path.parent
        if parent == current_path:
            # reached root
            break
        current_path = parent

    return files


def get_global_gitignore() -> Path | None:
    try:
        path = subprocess.check_output(["git", "config", "--get", "core.excludesfile"], text=True).strip()
        return Path(path).expanduser()
    except Exception:
        # Most likely the user doesn't have git installed, or it's not configured
        # correctly. In this case we don't want to bug the user with irrelevant
        # warnings, so just ignore completely.
        return None
