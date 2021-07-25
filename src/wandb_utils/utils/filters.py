from typing import List, Tuple, Union, Dict, Any, Optional
import wandb
import logging
import pathlib

logger = logging.getLogger(__name__)


class RunFilter(object):
    def __call__(self, run: wandb.apis.public.Run) -> bool:
        """Whether to take the run or not"""

        return True


class NameBasedRunFilter(RunFilter):
    def __init__(
        self,
        not_allowed_names: Optional[List[str]] = None,
        allowed_names: Optional[List[str]] = None,
    ):
        super().__init__()

        if bool(not_allowed_names) == bool(allowed_names):
            raise ValueError(
                "Exactly one of not_allowed_names or allowed_names should be passed"
            )
        self.allowed_names = set(allowed_names or [])
        self.not_allowed_names = set(not_allowed_names or [])
        self.allowed_branch = bool(allowed_names)

    def __call__(self, run: wandb.apis.public.Run) -> bool:
        if self.allowed_branch:
            return run.id in self.allowed_names
        else:

            return run.id not in self.not_allowed_names


logger = logging.getLogger(__name__)


class FileFilter(object):
    def __call__(
        self,
        run: Union[wandb.apis.public.File, pathlib.Path, pathlib.PurePath],
    ) -> bool:
        """Whether to take the file or not"""

        return True


class GlobBasedFileFilter(FileFilter):
    def __init__(
        self,
        include_filter: Optional[List[str]] = None,
        exclude_filter: Optional[List[str]] = None,
    ):
        self.allowed_globs = set(include_filter or [])
        self.not_allowed_globs = set(exclude_filter or [])

    def match(
        self,
        path: Union[pathlib.Path, pathlib.PurePath],
        globs: List[str],
    ) -> bool:

        for glob in globs:
            if path.match(glob):
                return True

        return False

    def __call__(
        self,
        file_: Union[
            str, wandb.apis.public.File, pathlib.Path, pathlib.PurePath
        ],
    ) -> bool:
        include_match = True
        exclude_match = False
        match = None

        if isinstance(file_, str):
            file_ = pathlib.PurePath(file_)
        elif isinstance(file_, wandb.apis.public.File):
            file_ = pathlib.PurePath(file_.name)

        if self.allowed_globs:
            include_match = self.match(file_, list(self.allowed_globs))

        if self.not_allowed_globs:
            exclude_match = self.match(file_, list(self.not_allowed_globs))
        # 1, 0 => True
        # 1, 1 => False
        # 0, 1 => False
        # 0, 0 => False
        match = include_match and (not exclude_match)

        return match
