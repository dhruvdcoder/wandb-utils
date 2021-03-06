from typing import List, Tuple, Union, Dict, Any, Optional
from .file_filter import FileFilter
import pathlib

import wandb


class GlobBasedFileFilter(FileFilter):
    def __init__(
        self,
        not_allowed_globs: Optional[List[str]] = None,
        allowed_globs: Optional[List[str]] = None,
    ):
        if bool(not_allowed_globs) == bool(allowed_globs):
            raise ValueError(
                "Exactly one of not_allowed_names or allowed_names should be passed"
            )
        self.allowed_globs = set(allowed_globs or [])
        self.not_allowed_globs = set(not_allowed_globs or [])

    def match(self, path: str, globs: List[str]) -> bool:
        path = pathlib.PurePath(path)

        for glob in globs:
            if path.match(glob):
                return True

        return False

    def __call__(self, file_: wandb.apis.public.File) -> bool:

        if self.allowed_globs:
            return self.match(file_, self.allowed_globs)
        else:
            return not self.match(file_, self.not_allowed_globs)
