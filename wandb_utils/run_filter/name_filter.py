from typing import List, Tuple, Union, Dict, Any, Optional
from .run_filter import RunFilter
import wandb
import logging

logger = logging.getLogger(__name__)


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
