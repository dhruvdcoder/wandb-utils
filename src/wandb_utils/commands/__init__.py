from typing import List, Tuple, Union, Dict, Any, Optional, Callable
from .wandb_utils import wandb_utils, wandb_utils_chain, processor
from .best_models import (
    find_best_model_command,
    find_best_model_command_chained,
)
from .all_data import get_all_data_command, get_all_data_command_chained
from .from_file import get_from_file_command, get_from_file_chained
from .filter import filter_df_chained
from .download_from_wandb import download_run_from_wandb_command
from .print import print_chained
from .backup import rclone
from .run_dir import get_run_dir_command
import click

wandb_utils.add_command(find_best_model_command)
wandb_utils.add_command(get_all_data_command)
wandb_utils.add_command(get_from_file_command)
wandb_utils.add_command(download_run_from_wandb_command)
wandb_utils.add_command(rclone)
wandb_utils.add_command(get_run_dir_command)


wandb_utils_chain.add_command(get_all_data_command_chained)
wandb_utils_chain.add_command(find_best_model_command_chained)
wandb_utils_chain.add_command(get_from_file_chained)
wandb_utils_chain.add_command(filter_df_chained)
wandb_utils_chain.add_command(print_chained)
