import logging
import os
import sys
import wandb

if os.environ.get("WANDB_UTILS_DEBUG"):
    LEVEL = logging.DEBUG
else:
    level_name = os.environ.get("WANDB_UTILS_LOG_LEVEL", "INFO")
    LEVEL = logging._nameToLevel.get(level_name, logging.INFO)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s", level=LEVEL
)


from wandb_utils.commands import wandb_utils, wandb_slurm
