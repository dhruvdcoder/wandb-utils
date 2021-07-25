import wandb
import pandas as pd
import argparse
from pathlib import Path
import sys, os
from wandb_utils.run_filter import NameBasedRunFilter, RunFilter
from wandb_utils.file_filter import GlobBasedFileFilter, FileFilter
import tqdm
import logging

if os.environ.get("WANDB_UTILS_DEBUG"):
    LEVEL = logging.DEBUG
else:
    level_name = os.environ.get("WANDB_UTILS_LOG_LEVEL", "INFO")
    LEVEL = logging._nameToLevel.get(level_name, logging.INFO)


logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=LEVEL,
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def readlines(file_: str):
    with open(file_) as f:
        lines = f.read().split()

    return lines


def get_args():
    parser = argparse.ArgumentParser(
        description="Remove saved files on the server without removing the run."
        ' The command supports run and file filters. "Allowed" in the filter means'
        " that the filter is of positive type, i.e., it returns true for things that pass"
        " that filter. In context of this command, the things that pass the filter"
        " get deleted."
    )
    parser.add_argument(
        "-e", "--entity", required=True, help="Wandb entity (username or team)"
    )
    parser.add_argument(
        "-p",
        "--project",
        required=True,
        type=str,
        help="Wandb project",
    )
    parser.add_argument(
        "-s",
        "--sweep",
        required=False,
        type=str,
        help="Wandb sweep (default:None)",
    )
    run_spec_group = parser.add_mutually_exclusive_group()
    run_spec_group.add_argument(
        "--allowed_runs",
        type=readlines,
        help="Path to a file containing allowed runs (run_ids) with each run_id on a separate line.",
    )
    run_spec_group.add_argument(
        "--not_allowed_runs",
        type=readlines,
        help="Path to a file containing not allowed runs with each run_id on a separate line.",
    )
    file_spec_group = parser.add_mutually_exclusive_group()
    file_spec_group.add_argument(
        "--allowed_files_globs",
        type=readlines,
        help="Path to a file containing allowed globs with each glob on a separate line.",
    )
    file_spec_group.add_argument(
        "--not_allowed_files_globs",
        type=readlines,
        help="Path to a file containing not allowed globs with each glob on a separate line.",
    )

    return parser.parse_args()


def main(args):
    api = wandb.Api({"entity": args.entity, "project": args.project})
    # filters
    run_filter = (
        NameBasedRunFilter(
            allowed_names=args.allowed_runs,
            not_allowed_names=args.not_allowed_runs,
        )
        if (bool(args.allowed_runs) or bool(args.not_allowed_runs))
        else RunFilter()
    )

    file_filter = (
        GlobBasedFileFilter(
            not_allowed_globs=args.not_allowed_files_globs,
            allowed_globs=args.allowed_files_globs,
        )
        if (
            bool(args.allowed_files_globs)
            or bool(args.not_allowed_files_globs)
        )
        else FileFilter()
    )

    if args.sweep:
        all_runs = api.sweep(f"{args.project}/{args.sweep}").runs
    else:
        all_runs = api.runs(f"{args.project}")

    logger.info(f"{len(all_runs)} total runs found.")
    runs = [r for r in tqdm.tqdm(all_runs) if run_filter(r)]
    logger.info(f"{len(runs)} left after filtering")

    for run in tqdm.tqdm(runs, desc="Runs processed"):
        files_to_delete = [f for f in run.files() if file_filter(f.name)]

        for file_ in files_to_delete:
            logger.debug(
                f"Deleting {args.entity}/{args.project}/{run.id}/{file_}"
            )
            file_.delete()


def run():
    main(get_args())


if __name__ == "__main__":
    run()
