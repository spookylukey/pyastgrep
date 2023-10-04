"""
Directory walker, with smart behaviour for ignoring files.

This is based on ripgrep behaviour:

- Automatically respect global and local `.gitignore` files
- Automatically ignore hidden files

With some known differences/unimplemented features/bugs:

- doesn't yet support `.ignore` files
- ripgrep does not respect `.gitignore` files if the starting directory is outside a git repo
  https://github.com/BurntSushi/ripgrep/issues/1109 but we do
- ripgrep considers Windows files with hidden attribute to be hidden, we do not yet.
- if starting inside hidden folders, we return nothing by default because the parent is hidden,
  but ripgrep doesn't do this.

"""
from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Union, overload

from pathspec import GitIgnoreSpec, PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WalkError:
    path: Path
    exception: Exception


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

    def __repr__(self) -> str:
        return f"<DirectoryPathSpec {self.location!r} {self.pathspec!r}>"


class GlobalGitIgnoreSpec(GitIgnoreSpec):
    # This subclass exists currently only for the sake of debugging
    pass


PathSpecLike = Union[PathSpec, DirectoryPathSpec]


class _Default:
    """
    Sentinel for default values to function/method args
    """


DEFAULT: Any = _Default()


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
        pathspecs: list[PathSpecLike] = DEFAULT,
        init_global_pathspecs: bool = True,
        start_directory: Path | None = None,
        working_dir: Path | None = None,
        absolute_base: bool = False,
        include_hidden: bool = False,
        respect_global_ignores: bool = True,
        respect_vcs_ignores: bool = True,
    ):
        # DirWalker is immutable outside __init__
        self.glob: str = glob
        if pathspecs is DEFAULT:
            pathspecs = []
        if init_global_pathspecs:
            if respect_global_ignores:
                if respect_vcs_ignores:
                    global_gitignore = get_global_gitignore()
                    if global_gitignore and global_gitignore.exists():
                        pathspecs.append(pathspec_for_gitignore(global_gitignore, is_global_gitignore=True))
            # POSIX hidden files:
            if not include_hidden:
                # TODO we should probably use a different mechanism for hidden
                # files, this causes problems and doesn't cope with Windows
                # hidden files.
                pathspecs.append(PathSpec([GitWildMatchPattern(".*")]))
        self.pathspecs: list[PathSpecLike] = pathspecs
        self.start_directory: Path | None = start_directory
        self.working_dir: Path | None = working_dir
        self.absolute_base: bool = absolute_base
        self.respect_vcs_ignores: bool = respect_vcs_ignores

    def for_dir(self, directory: Path, working_dir: Path) -> DirWalker:
        """
        Return a new DirWalker, customised for the directory.
        """
        # Here we keep the already loaded global gitignore, and add any
        # more needed, up to and including the current directory.
        base_directory = directory.resolve()
        if self.respect_vcs_ignores:
            pathspecs = self.pathspecs + [
                pathspec_for_gitignore(ignorepath)
                for ignorepath in find_gitignore_files(base_directory, recurse_up=True)
            ]
        else:
            pathspecs = self.pathspecs
        # We also need to add a negative override to ensure that paths specified
        # directly are not ignored.
        if directory != Path("."):
            # TODO this doesn't work in all cases, e.g. if an exclude is specified
            # in a subdirectory `.gitignore` which matches the passed in directory.
            pathspecs = [add_negative_dir_pattern(pathspec, directory) for pathspec in pathspecs]

        return self._clone(
            pathspecs=pathspecs,
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
        if self.respect_vcs_ignores:
            extra_pathspecs: list[PathSpecLike] = [
                pathspec_for_gitignore(ignorepath) for ignorepath in find_gitignore_files(directory, recurse_up=False)
            ]
        else:
            extra_pathspecs = []

        return self._clone(
            pathspecs=self.pathspecs + extra_pathspecs,
            start_directory=directory,
        )

    def walk(self) -> Iterable[Path | WalkError]:
        if self.start_directory is None or self.working_dir is None:
            raise AssertionError("Must use `for_dir` before `walk`")
        for filepath in self.start_directory.glob(self.glob):
            if filepath.is_symlink():
                # Follow default behaviour of ripgrep, and avoid issues with
                # `resolve().relative_to(working_dir)
                logger.debug("Ignoring symlink %s", filepath)
                continue
            if filepath.is_file():
                pathspec_matched = False
                for pathspec in self.pathspecs:
                    if pathspec.match_file(filepath):
                        pathspec_matched = True
                        logger.debug("Ignoring path %s because it matches pathspec %s", filepath, pathspec)
                        break
                if pathspec_matched:
                    continue
                if self.absolute_base:
                    yield filepath
                else:
                    yield filepath.resolve().relative_to(self.working_dir)

        for subdir in tolerant_iterdir(self.start_directory):
            if not isinstance(subdir, Path):
                yield subdir
                continue
            try:
                if subdir.is_symlink():
                    logger.debug("Ignoring symlink %s", subdir)
                    continue
            except PermissionError:
                logger.debug("Ignoring unreadable file %s", subdir)
                continue
            if subdir.is_dir():
                pathspec_matched = False
                for pathspec in self.pathspecs:
                    if pathspec.match_file(subdir):
                        pathspec_matched = True
                        logger.debug("Ignoring path %s because it matches pathspec %s", subdir, pathspec)
                        break
                if pathspec_matched:
                    continue
                yield from self.for_subdir(subdir).walk()

    def _clone(
        self,
        *,
        pathspecs: list[PathSpecLike],
        start_directory: Path,
        working_dir: Path = DEFAULT,
        absolute_base: bool = DEFAULT,
    ) -> DirWalker:
        return DirWalker(
            glob=self.glob,
            pathspecs=pathspecs,
            init_global_pathspecs=False,
            start_directory=start_directory,
            working_dir=self.working_dir if working_dir is DEFAULT else working_dir,
            absolute_base=self.absolute_base if absolute_base is DEFAULT else absolute_base,
            respect_vcs_ignores=self.respect_vcs_ignores,
        )


def tolerant_iterdir(directory: Path) -> Iterable[Path | WalkError]:
    try:
        yield from directory.iterdir()
    except PermissionError as e:
        yield WalkError(directory, e)


def pathspec_for_gitignore(gitignore_file: Path, is_global_gitignore: bool = False) -> PathSpec | DirectoryPathSpec:
    try:
        with open(gitignore_file) as fp:
            if is_global_gitignore:
                return GlobalGitIgnoreSpec.from_lines(fp)
            else:
                return DirectoryPathSpec(gitignore_file.parent, GitIgnoreSpec.from_lines(fp))
    except PermissionError:
        # Silently ignoring unreadable .gitignore is probably our best option
        logger.debug("Ignoring unreadable gitignore %s", gitignore_file)
        return DirectoryPathSpec(gitignore_file.parent, GitIgnoreSpec.from_lines([]))


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
        try:
            if candidate.exists():
                files.append(candidate)
        except PermissionError:
            # Usually because we can't read from the dir, so silently ignore
            logger.debug("Ignoring unreadable dir %s", current_path)
        if not recurse_up:
            break
        try:
            if (current_path / ".git").exists():
                # Found the root git repo, stop searching
                break
        except PermissionError:
            pass
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
