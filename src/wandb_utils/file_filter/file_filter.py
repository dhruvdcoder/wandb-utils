from typing import Union
import wandb
import logging
import pathlib

logger = logging.getLogger(__name__)


class FileFilter(object):
    def __call__(
        self,
        run: Union[wandb.apis.public.File, pathlib.Path, pathlib.PurePath],
    ) -> bool:
        """Whether to take the file or not"""

        return True
