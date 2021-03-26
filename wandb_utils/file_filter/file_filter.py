import wandb
import logging

logger = logging.getLogger(__name__)


class FileFilter(object):
    def __call__(self, run: wandb.apis.public.File) -> bool:
        """Whether to take the file or not"""

        return True
