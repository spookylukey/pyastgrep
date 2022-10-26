from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Generator

from pathspec import GitIgnoreSpec, PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern


class DirWalker:
    """
    Walks a directory recursively, returning files that match a glob,
    while automatically respecting dot-ignore files
    """

    def __init__(
        self,
        *,
        glob: str,
        pathspecs: list[PathSpec] = None,
        init_global_pathspecs: bool = True,
        start_directory: Path | None = None,
    ):
        # DirWalker is immutable outside __init__
        self.glob: str = glob
        if pathspecs is None:
            pathspecs = []
        if init_global_pathspecs:
            global_gitignore = get_global_gitignore()
            if global_gitignore:
                pathspecs.append(pathspec_for_gitignore(global_gitignore))
            # POSIX hidden files:
            pathspecs.append(PathSpec([GitWildMatchPattern(".*")]))
        self.pathspecs: list[PathSpec] = pathspecs
        self.start_directory: Path | None = start_directory

    def for_dir(self, directory: Path) -> DirWalker:
        """
        Return a new DirWalker, customised for the directory.
        """
        return DirWalker(
            glob=self.glob,
            # Here we keep the already loaded global gitignore, and add any
            # more needed, up to and including the current directory
            pathspecs=self.pathspecs
            + [pathspec_for_gitignore(ignorepath) for ignorepath in find_gitignore_files(directory, recurse_up=True)],
            init_global_pathspecs=False,
            start_directory=directory,
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
        extra_pathspecs = [
            pathspec_for_gitignore(ignorepath) for ignorepath in find_gitignore_files(directory, recurse_up=False)
        ]
        return DirWalker(
            glob=self.glob,
            pathspecs=self.pathspecs + extra_pathspecs,
            init_global_pathspecs=False,
            start_directory=directory,
        )

    def walk(self) -> Generator[Path, None, None]:
        if self.start_directory is None:
            raise AssertionError("Must use `for_dir` before `walk`")
        for filepath in self.start_directory.glob(self.glob):
            if any(pathspec.match_file(filepath.name) for pathspec in self.pathspecs):
                continue
            if filepath.is_file():
                yield filepath
        for subdir in self.start_directory.iterdir():
            if any(pathspec.match_file(subdir.name) for pathspec in self.pathspecs):
                continue
            if subdir.is_dir():
                yield from self.for_subdir(subdir).walk()


def pathspec_for_gitignore(gitignore_file: Path) -> PathSpec:
    with open(gitignore_file) as fp:
        return GitIgnoreSpec.from_lines(fp)


def find_gitignore_files(working_dir: Path, *, recurse_up: bool = True) -> list[Path]:
    """
    For a given working dir, returns a list of .gitignore files
    that apply to it.
    """
    files = []

    # Not 100% sure this is correct or what ripgrep does,
    # but it probably covers the most common setups
    current_path = working_dir.resolve()
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
        return Path(subprocess.check_output(["git", "config", "--get", "core.excludesfile"], text=True).strip())
    except Exception:
        # Most likely the user doesn't have git installed, or it's not configured
        # correctly. In this case we don't want to bug the user with irrelevant
        # warnings, so just ignore completely.
        return None
