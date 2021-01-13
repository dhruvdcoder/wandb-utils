import wandb
import pandas as pd
import argparse
from pathlib import Path
import sys
from wandb_utils.misc import create_multiple_run_sweep_for_run
import logging

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO,
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-e", "--entity", required=True, help="Wandb entity (username or team)"
    )
    parser.add_argument(
        "-p",
        "--project",
        required=True,
        type=str,
        help="Wandb project (default:None)",
    )
    parser.add_argument(
        "-t",
        "--sweep_name",
        required=True,
        type=str,
        help="Sweep name of the sweep to create. ",
    )
    parser.add_argument(
        "--wandb_tags",
        nargs="+",
        help="Extra tags for the runs of the new sweep. ",
    )
    parser.add_argument(
        "-r",
        "--run",
        required=False,
        type=str,
        help="Wandb run id (default:None)",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        required=True,
        type=Path,
        help="File where model config will be kept",
    )
    parser.add_argument(
        "-s",
        "--sweep",
        type=str,
        help="Sweep in which to search for the best model."
        "Required if not supplying run. (default:None)",
    )
    parser.add_argument(
        "-m",
        "--metric",
        required=False,
        type=str,
        help="Name of the metric to sort by. "
        "Required if not supplying run. (default:None)",
    )
    parser.add_argument(
        "--maximum",
        action="store_true",
        help="Whether the best is mininum or maximum (default:False)",
    )
    parser.add_argument(
        "--relative_path",
        type=str,
        default="training_dumps/config.json",
        help="Path of the config file on wandb. (default:training_dumps/config.json)",
    )

    return parser.parse_args()


def main(args):
    create_multiple_run_sweep_for_run(**vars(args))


def run():
    main(get_args())


if __name__ == "__main__":
    run()
