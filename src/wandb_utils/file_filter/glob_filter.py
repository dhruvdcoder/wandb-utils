from typing import List, Tuple, Union, Dict, Any, Optional
from .file_filter import FileFilter
import pathlib

import wandb


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
