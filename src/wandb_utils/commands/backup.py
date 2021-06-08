# System
import sys
import time

# Processes/Threads
import pyclone

# Data
import re

# Logging
import tqdm


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
    parser.add_argument(
        "--seed_parameters",
        nargs="+",
        help=(
            "Name of the seed parameters, "
            "ex: --seed_parameters pytorch_seed numpy_seed random_seed (default:None)"
        ),
    )
    parser.add_argument(
        "--include_packages",
        nargs="+",
        default=[],
        help=("Extra packages to include for allennlp"),
    )
    parser.add_argument(
        "--delete_keys",
        nargs="+",
        default=[],
        help=("Keys to be deleted. Supports nested keys as a.b.c"),
    )
    parser.add_argument(
        "--fixed_overrides",
        type=str,
        default="{}",
        help=(
            "a json(net) structure used to override the experiment configuration, e.g., "
            "'{\"iterator.batch_size\": 16}'.  Nested parameters can be specified either"
            " with nested dictionaries or with dot syntax."
            " For more details see --overrides "
            "of https://github.com/allenai/allennlp/blob/main/allennlp/commands/train.py "
        ),
    )

    return parser.parse_args()


# Create an instance using rclone with defaults (e.g. rclone at host level, no STDERR redirect, and a minimal message buffer size.)
rclone = pyclone.PyClone()

# Copy files from local to remote
rclone.copy(
    source="/mnt/familyPhotos",
    remote="googleDrive",
    path="/backups/familyPhotos",
)

try:

    # Overall progress
    totalProgress = tqdm.tqdm(
        leave=False, unit="pct", unit_scale=False, total=100
    )
    totalProgress.set_description("Total transfer")

    # Dictionary of progress bars
    pbars = []

    # Read message buffer

    while rclone.tailing():

        # Buffer contents found

        if rclone.readline():

            # Transfer activity found
            transfers = rclone.line.get("stats", {}).get("transferring", [])
            transfersCount = len(transfers)

            # Update count of progress bars
            pbarsCount = len(pbars)

            # Update total progress
            statusMatch = None

            if rclone.line.get("msg"):

                # Parse status message
                statusMatch = re.search(
                    ".*Transferred:[\s]+.*[\s]+([0-9]+)%.*[\s]+ETA[\s]+.*",
                    rclone.line["msg"],
                )

                # Parse match found

                if statusMatch:

                    # Update total percentage
                    totalProgress.n = int(statusMatch.group(1))
                    totalProgress.update()

                    pass  # END IF : MATCH

                pass  # END IF : MESSAGE
            del statusMatch

            # Add progress bars

            if transfersCount > pbarsCount:
                pbars.extend(
                    [
                        tqdm.tqdm(leave=False, unit="b", unit_scale=True)
                        for i in range(transfersCount - pbarsCount)
                    ]
                )
                pass  # END IF : ADD PROGRESS BARS

            # Iterate list of transfers and add a reciprocal index

            for i, t in enumerate(transfers):

                # Update percentage and name for current progress bar
                pbars[i].total = t["size"]
                pbars[i].n = t["bytes"]
                pbars[i].set_description(t["name"])
                pbars[i].update()

                pass  # END FOR

            # Remove progress bars

            if transfersCount < pbarsCount:
                [pb.close() for pb in pbars[(pbarsCount - transfersCount) :]]
                del pbars[(pbarsCount - transfersCount) :]
                pass  # END ELIF : REMOVE PROGRESS BARS

            pass  # END IF : READ LINE

        # Wait 0.5 seconds until we query message buffer again
        time.sleep(0.5)

        pass  # END WHILE LOOP

    # Refresh total progress
    totalProgress.refresh()

    pass  # END TRY

except KeyboardInterrupt:
    print()
    pass  # END KEYBOARD INTERRUPT

finally:

    # Remove any remaining progress bars
    [pb.close() for pb in pbars[(pbarsCount - transfersCount) :]]
    totalProgress.close()
    del totalProgress, pbars

    # Clean-up
    rclone.stop()

    pass  # END FINALLY
