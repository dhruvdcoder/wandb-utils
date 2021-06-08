import logging
import os
import sys

if os.environ.get("WANDB_UTILS_DEBUG"):
    LEVEL = logging.DEBUG
else:
    level_name = os.environ.get("WANDB_UTILS_LOG_LEVEL", "INFO")
    LEVEL = logging._nameToLevel.get(level_name, logging.INFO)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s", level=LEVEL
)

from wandb_utils.commands.wandb_utils import wandb_utils as wandb_utils_cli

wandb_utils_cli(prog_name="python -m wandb_utils")
