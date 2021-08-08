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
from .common import processor
from wandb_utils.file_filter import FileFilter, GlobBasedFileFilter
import logging
import tqdm
import pexpect
import threading
import json


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

    def command(
        self,
        action: str,
        source: str,
        target: str = "",
        target_remote: str = "",
        source_remote: str = "",
    ) -> str:
        cmdLine = f'bash -c "{self.__binPath} {self.__flagsToString()} --stats=1s --use-json-log --verbose=1 {action} {source_remote+":" if source_remote else ""}{source if source else ""} {target_remote+":" if target_remote else ""}{target} {self.__binSuffix}"'
        logger.debug(f"Starting following command:\n{cmdLine}")

        return cmdLine

    def __threadedProcess(
        self,
        *,
        action: str,
        source: str,
        remote: str,
        path: str,
        source_remote: str = "",
    ) -> None:
        """

        The rclone process runs under this method as a separate thread, which is launched by :any:`PyClone.__launchThread()`.
        All available output from `rclone` is placed into :any:`the message buffer <PyClone.__messages>` from this method.


        Parameters
        ----------
        action : :obj:`str`
                Provided by a wrapper method such as :any:`PyClone.copy()` and passed to `rclone`.

        source : :obj:`str`
                Files to transfer.

        remote : :obj:`str`
                Configured service name.

        path : :obj:`str`
                Destination to save to.

        """

        logger.debug(
            f"__threadedProcess() : action={action}, source={source}, remote={remote}, path={path}"
        )

        logger.debug("touch() : acquire lock")
        self.__lock.acquire()

        # It takes a moment for the process to spawn
        self.__proc = True

        # cmdLine = f'bash -c "{self.__binPath} {self.__flagsToString()} --stats=1s --use-json-log --verbose=1 {action} {( source if source else "" )} {remote}:{path} {self.__binSuffix}"'
        cmdLine = self.command(
            action,
            source,
            path,
            source_remote=source_remote,
            target_remote=remote,
        )
        logger.debug(f"__threadedProcess() : spawn process : {cmdLine}")
        self.__proc = pexpect.spawn(
            cmdLine,
            echo=False,
            timeout=None,
        )

        # Fill buffer

        while not self.__proc.eof():

            line = None

            # Parse JSON
            try:
                raw_line = self.__proc.readline().decode().strip()
                line = json.loads(raw_line)
                logger.debug("__threadedProcess() : parsed JSON line.")
                pass  # END TRY

            # Probably noise from Docker Compose
            except json.JSONDecodeError as e:
                logger.debug(
                    f"__threadedProcess() : exception (JSON decoding error) : {e}"
                )
                logger.debug(f"Unable to decode: {raw_line}")
                line = {}
                pass  # END EXCEPTION

            except Exception as e:
                logger.error(f"__threadedProcess() : {e}")

                break
                pass  # END EXCEPTION

            finally:
                logger.debug(
                    f"__threadedProcess() : append message to buffer : {line}"
                )
                self.__messages.append(line)
                pass  # END FINALLY

            pass  # END WHILE LOOP

        logger.debug("__threadedProcess() : close process")
        self.__proc.close(force=True)

        logger.debug("__threadedProcess() : release lock")
        self.__lock.release()

        pass  # END PRIVATE METHOD : Threaded process

    def __launchThread(
        self, *, action, source, remote, path, source_remote: str = ""
    ):
        """

        This sets up and starts a thread with :any:`PyClone.__threadedProcess()` used as the target,
        and is used by convenience/wrapper methods such as:

        * :any:`PyClone.copy()`

        * :any:`PyClone.sync()`

        * :any:`PyClone.delete()`

        * :any:`PyClone.purge()`


        Parameters
        ----------
        action : :obj:`str`
                Provided by a wrapper method such as :any:`PyClone.copy()` and passed to `rclone`.

        source : :obj:`str`
                Files to transfer.

        remote : :obj:`str`
                Configured service name.

        path : :obj:`str`
                Destination to save to.

        """

        logger.debug(
            f"__launchThread() : action={action}, source={source}, remote={remote}, path={path}"
        )
        self.__thread = threading.Thread(
            target=self.__threadedProcess,
            kwargs={
                "action": action,
                "source": source,
                "remote": remote,
                "path": path,
                "source_remote": source_remote,
            },
        )
        logger.debug(f"__launchThread() : start thread")
        self.__thread.start()

        pass  # END PRIVATE METHOD : Launch thread

    def copy(
        self,
        source: str,
        target: str,
        source_remote: str,
        target_remote: str,
    ) -> None:
        self.__launchThread(
            action="copy",
            source=source,
            remote=target_remote,
            path=target,
            source_remote=source_remote,
        )

    def move(
        self,
        source: str,
        target: str,
        source_remote: str,
        target_remote: str,
    ) -> None:
        self.__launchThread(
            action="move",
            source=source,
            remote=target_remote,
            path=target,
            source_remote=source_remote,
        )


def copy_to_remote(
    rclone: pyclone.PyClone,
    source: pathlib.Path,
    target: Optional[pathlib.Path] = None,
    source_remote: Optional[str] = None,
    target_remote: Optional[str] = None,
) -> bool:

    # Copy files from local to remote
    rclone.copy(
        source=str(source),
        target=str(target) if target else "",
        source_remote=source_remote if source_remote else "",
        target_remote=target_remote if target_remote else "",
    )

    errors = 0
    try:
        # Ref: https://gitlab.com/ltgiv/pyclone/-/blob/master/examples/progress-tqdm.py

        # Overall progress
        totalProgress = tqdm.tqdm(
            leave=False, unit="pct", unit_scale=False, total=101
        )
        totalProgress.set_description("Total transfer")

        # Dictionary of progress bars
        pbars = []

        # Read message buffer

        while rclone.tailing():

            # Buffer contents found

            if rclone.readline():

                # Transfer activity found
                transfers = rclone.line.get("stats", {}).get(
                    "transferring", []
                )
                errors += int(rclone.line.get("stats", {}).get("errors", 0))

                if errors:
                    pass

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
                    elif (
                        rclone.line.get("msg")
                        == "There was nothing to transfer"
                    ):
                        logger.info("There was nothing to transfer.")

                        break

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

                    if "name" in t:  # update only if t != {}
                        pbars[i].total = t.get("size", 0)
                        pbars[i].n = t.get("bytes", 0)
                        pbars[i].set_description(t["name"])
                        pbars[i].update()

                # Remove progress bars

                # if transfersCount < pbarsCount:
                #    [
                #        pb.close()
                #        for pb in pbars[(pbarsCount - transfersCount) :]
                #    ]
                #    del pbars[(pbarsCount - transfersCount) :]

            # Wait 0.5 seconds until we query message buffer again
            time.sleep(0.5)

        # Refresh total progress
        totalProgress.refresh()

    except KeyboardInterrupt:
        print()

    finally:

        # Remove any remaining progress bars
        # [pb.close() for pb in pbars[(pbarsCount - transfersCount) :]]

        # Clean-up
        rclone.stop()

    return not errors > 0


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
@click.option("--source_remote", type=str, default="")
@click.option(
    "--target",
    type=click.Path(path_type=pathlib.Path),
)
@click.option("--target_remote", type=str, default="")
@click.pass_obj
def copy(
    rclone: PyClone,
    source: pathlib.Path,
    source_remote: str,
    target: Optional[pathlib.Path],
    target_remote: str,
) -> None:
    """
    Copy from SOURCE to REMOTE:TARGET using rclone.
    """
    error = copy_to_remote(
        rclone,
        source,
        target,
        source_remote,
        target_remote,
    )

    if error:
        raise RuntimeError(
            "rclone copy produced errors. Set in debug model and check the log."
        )


@rclone.command("move")
@click.argument("source", type=click.Path(path_type=pathlib.Path))
@click.option("--source_remote", type=str, default="")
@click.option(
    "--target",
    type=click.Path(path_type=pathlib.Path),
)
@click.option("--target_remote", type=str, default="")
@click.pass_obj
def move(
    rclone: PyClone,
    source: pathlib.Path,
    source_remote: str,
    target: Optional[pathlib.Path],
    target_remote: str,
) -> None:
    """
    Copy from SOURCE to REMOTE:TARGET using rclone.
    """
    error = copy_to_remote(
        rclone,
        source,
        target,
        source_remote,
        target_remote,
    )

    if error:
        raise RuntimeError(
            "rclone copy produced errors. Set in debug model and check the log."
        )
