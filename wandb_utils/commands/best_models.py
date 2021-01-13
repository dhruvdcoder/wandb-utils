import wandb
import pandas as pd
import argparse
from pathlib import Path
import sys
from wandb_utils.misc import find_best_models_in_sweeps
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
        "-m",
        "--metric",
        required=True,
        type=str,
        help="Name of the metric to sort by (default:None)",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        required=False,
        type=Path,
        help="File to which the run names will be written/appended."
        " If not provided, the name will be printed on the console. (default:None)",
    )
    parser.add_argument(
        "-a",
        "--append",
        required=False,
        action="store_true",
        help="Set to append to file instead of overwritting (default:False)",
    )

    return parser.parse_args()


def main(args):
    df = find_best_models_in_sweeps(args.entity, args.project, args.metric)
    logger.info(
        f"Following are the models:\n{df[['sweep', 'run', args.metric]]}"
    )
    existing_runs = []

    if args.output_file and args.append:
        logger.info(f"Appending to existing file.")
        with open(args.output_file, "r") as f:
            existing_runs = [word.strip() for word in f.read().split("\n")]

    if args.output_file:
        f = open(args.output_file, "w")
        logger.info(f"Writing to {args.output_file}.")
    else:
        logger.info(f"No output file, printing on stdout.")
        f = sys.stdout

    for run in set(existing_runs + df["run"].values.tolist()):
        if run:  # ignore empty strings
            f.write(f"{run}\n")


def run():
    main(get_args())


if __name__ == "__main__":
    run()
