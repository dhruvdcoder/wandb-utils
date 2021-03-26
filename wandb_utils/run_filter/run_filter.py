import wandb
import logging

logger = logging.getLogger(__name__)


class RunFilter(object):
    def __call__(self, run: wandb.apis.public.Run) -> bool:
        """Whether to take the run or not"""

        return True
