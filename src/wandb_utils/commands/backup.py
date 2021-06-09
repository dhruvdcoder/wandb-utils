import sys
import time
import pyclone
import re
import tqdm
from typing import List, Tuple, Union, Dict, Any, Optional
import click
import wandb
import pandas as pd
import argparse
import pathlib
import sys
from .wandb_utils import (
    wandb_utils,
    pass_api_wrapper,
    pass_api_and_info,
    config_file_decorator,
)
from wandb_utils.file_filter import FileFilter, GlobBasedFileFilter
import logging
import tqdm

logger = logging.getLogger(__name__)

from collections.abc import Sequence


def _seq_but_not_str(obj: Any) -> bool:
    return isinstance(obj, Sequence) and not isinstance(
        obj, (str, bytes, bytearray)
    )


class PyClone(pyclone.PyClone):
    """
    Same as `pyclone.PyClone` but with some methods overridden.
    """

    def __init__(
        self,
        *,
        binPath: str = None,
        binSuffix: str = "",
        messageBufferSize: int = 5,
        global_flags: Optional[Dict] = None,
    ):
        super().__init__(
            binPath=binPath,
            binSuffix=binSuffix,
            messageBufferSize=messageBufferSize,
        )

        if global_flags is not None:
            self.__flags.update(global_flags)

    def __flagsToString(self) -> str:

        r = ""

        for k, v in self.__flags.items():

            # Add value

            if v is not None:
                if _seq_but_not_str(v):  # List, Tuple etc.
                    if len(v) > 0:  # If empty, ignore.
                        for v_ in v:
                            r += f"--{k} {v_} "
                else:  # pure value like str, int, etc.
                    r += f"--{k} {v} "
            else:
                # Pure bool flag
                r += f"--{k} "

        logger.debug(f"__flagsToString() : return : {r}")

        return r


def copy_to_remote(
    rclone: pyclone.PyClone,
    source: pathlib.Path,
    remote: str,
    target: Optional[pathlib.Path] = None,
) -> None:

    # Copy files from local to remote
    breakpoint()
    rclone.copy(
        source=str(source),
        remote=remote,
        path=str(target) if target is not None else "",
    )

    try:
        # Ref: https://gitlab.com/ltgiv/pyclone/-/blob/master/examples/progress-tqdm.py

        # Overall progress
        totalProgress = tqdm.tqdm(
            leave=False, unit="pct", unit_scale=False, total=100
        )
        totalProgress.set_description("Total transfer")

        # Dictionary of progress bars
        pbars = []

        # Read message buffer
        breakpoint()

        while rclone.tailing():

            # Buffer contents found

            if rclone.readline():

                # Transfer activity found
                # breakpoint()
                transfers = rclone.line.get("stats", {}).get(
                    "transferring", []
                )
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

                del statusMatch

                # Add progress bars

                if transfersCount > pbarsCount:
                    pbars.extend(
                        [
                            tqdm.tqdm(leave=True, unit="b", unit_scale=True)
                            for i in range(transfersCount - pbarsCount)
                        ]
                    )

                # Iterate list of transfers and add a reciprocal index

                for i, t in enumerate(transfers):

                    # Update percentage and name for current progress bar
                    pbars[i].total = t["size"]
                    pbars[i].n = t["bytes"]
                    pbars[i].set_description(t["name"])
                    pbars[i].update()

                # Remove progress bars

                if transfersCount < pbarsCount:
                    [
                        pb.close()
                        for pb in pbars[(pbarsCount - transfersCount) :]
                    ]
                    del pbars[(pbarsCount - transfersCount) :]

            # Wait 0.5 seconds until we query message buffer again
            time.sleep(0.5)

        # Refresh total progress
        totalProgress.refresh()

    except KeyboardInterrupt:
        print()

    finally:

        # Remove any remaining progress bars
        [pb.close() for pb in pbars[(pbarsCount - transfersCount) :]]
        totalProgress.close()
        del totalProgress, pbars

        # Clean-up
        rclone.stop()


@click.group()
@click.option(
    "--include_filter",
    multiple=True,
    default=[],
    type=str,
    help="Glob string for files to include (can pass multiple). See https://rclone.org/filtering/ for details.",
)
@click.option(
    "--exclude_filter",
    multiple=True,
    default=[],
    type=str,
    help="Glob string for Files to exclude (can pass multiple). See https://rclone.org/filtering/ for details.",
)
@click.option(
    "--filter",
    multiple=True,
    default=[],
    type=str,
    help=(
        "Glob string for Files to use as --filter (can pass multiple). "
        "From rclone documentation:"
        "Each path/file name passed through rclone is matched against the combined filter list. "
        " At first match to a rule the path/file name is included or excluded and no further filter rules are processed for that path/file."
        " See https://rclone.org/filtering/ for details."
    ),
)
@click.option(
    "--dump",
    type=str,
    default=[],
    multiple=True,
    help=(
        "Used to dump internal variable of rclone for debugging. For instance, --dump filters will dump processed filters."
        "See: https://rclone.org/flags/"
    ),
)
@click.pass_context
@config_file_decorator()
def rclone(
    ctx: click.Context,
    include_filter: List[str],
    exclude_filter: List[str],
    filter: List[str],
    dump: List[str],
) -> None:
    """
    Perform operations on remote storage using Rclone.
    """
    ctx.obj = PyClone(
        global_flags={
            "include": include_filter,
            "exclude": exclude_filter,
            "filter": filter,
            "dump": dump,
        }
    )


@rclone.command("copy")
@click.argument("source", type=click.Path(path_type=pathlib.Path))
@click.argument("remote", type=str, default="")
@click.option(
    "--target",
    type=click.Path(path_type=pathlib.Path),
)
@click.pass_obj
def copy(
    rclone: PyClone,
    source: pathlib.Path,
    remote: str,
    target: Optional[pathlib.Path],
) -> None:
    """
    Copy from SOURCE to REMOTE:TARGET using rclone.
    """
    copy_to_remote(
        rclone,
        source,
        remote,
        target,
    )
