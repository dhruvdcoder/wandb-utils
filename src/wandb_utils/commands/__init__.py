from typing import List, Tuple, Union, Dict, Any, Optional, Callable
from .wandb_utils import wandb_utils
from .best_models import (
    best_model_command,
)
from .all_data import all_data_command
from .from_file import from_file_command
from .filter import filter_df
from .download_from_wandb import download_run_from_wandb_command
from .print import print_command
from .backup import rclone
from .run_dir import run_dir_command
from .files import files_command
from .slurm import wandb_slurm
import click

wandb_utils.add_command(best_model_command)
wandb_utils.add_command(all_data_command)
wandb_utils.add_command(from_file_command)
wandb_utils.add_command(download_run_from_wandb_command)
wandb_utils.add_command(files_command)
# wandb_utils.add_command(rclone)
wandb_utils.add_command(run_dir_command)


wandb_utils.add_command(filter_df)
wandb_utils.add_command(print_command)
