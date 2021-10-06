from typing import List, Tuple, Union, Dict, Any, Optional
from wandb_utils.version import VERSION
import click
import wandb
import pandas as pd
import argparse
import pathlib
import sys
from .common import LIST
from .wandb_utils import (
    pass_api_wrapper,
    pass_api_and_info,
    METRIC,
    Metric,
    processor,
    apply_decorators,
    config_file_decorator,
)
from wandb_utils.config import load_config
import logging
import os
import textwrap
import subprocess
import re
from click import pass_context

from jinja2 import Environment, Template, meta

logger = logging.getLogger(__name__)

SBATCH_TEMPLATE = """#!/bin/bash
{% if num_gpus -%}
#SBATCH --gres=gpu:{{ num_gpus }}
{% endif -%}
{% if partition -%}
#SBATCH --partition={{ partition }}
{% endif -%}
#SBATCH --cpus-per-task={{ cpus_per_task | default('3', true) }}
#SBATCH --mem={{ mem | default('12GB', true) }}
{%- if signals %}
#SBATCH --signal=B:{{ signals[0] }}@{{ inform_before_time | default('60', true) }}
{%- endif %}
{%- set complete_sweep_id_elements = [] %}
{%- if entity %}{% do complete_sweep_id_elements.append(entity) %}{% endif %}
{%- if project %}{% do complete_sweep_id_elements.append(project) %}{% endif %}
{%- do complete_sweep_id_elements.append(sweep) %}

#SBATCH --job-name={{ sweep }}
{%- if num_agents > 1 and not chain %}
#SBATCH --array=1-{{num_agents}}
#SBATCH --output={{ job_dir }}/%A_%a.out
{%- else %}
#SBATCH --output={{ job_dir }}/%j.out
{%- endif %}
{%- for arg in verbatim_args %}
#SBATCH --{{ arg }}
{%- endfor %}

{%- if signals %}
# trap the signal to the main BATCH script here.
sig_handler()
{
 echo "BATCH interrupted"
 wait # wait for all children, this is important!
}
{%- set signals_fullname = [] %}
{%- for sig in signals %}{% do signals_fullname.append('SIG'+sig) %}{% endfor %}
trap 'sig_handler' {{ signals_fullname |join(' ')}}
{%- endif %}

srun wandb agent {% if run_count %}--count {{ run_count }} {% endif %}{{ complete_sweep_id_elements | join('/') }}
"""

# ref: https://stackoverflow.com/questions/50499340/specify-options-and-arguments-dynamically
# Can use this with get_current_context()


class WandbUtilsSlurm(object):
    def __init__(
        self,
        api: wandb.PublicApi,
        entity: Optional[str],
        project: Optional[str],
        sweep: Optional[str],
        directory: pathlib.Path,
        sbatch_template: Optional[pathlib.Path],
    ) -> None:
        self.api = api
        self.entity = entity
        self.project = project
        self.sweep = sweep
        self.directory = directory
        self.sbatch_template = sbatch_template

        if self.sbatch_template is None:
            logger.info("sbatch_template not provided")
            local_template = self.directory / "sbatch.j2"
            local_template.parent.mkdir(parents=True, exist_ok=True)

            if local_template.exists() and local_template.is_file():
                logger.info(f"Reading sbatch_template from {local_template}")
                self.sbatch_template = local_template
                with open(self.sbatch_template) as f:
                    self.sbatch_template_str = f.read()
            else:
                logger.info(
                    f"Could not find sbatch_template at {local_template}"
                )
                global_template = (
                    pathlib.Path(
                        click.get_app_dir("wandb_utils", force_posix=True)
                    )
                    / "slurm"
                    / "sbatch.j2"
                )
                global_template.parent.mkdir(parents=True, exist_ok=True)

                if global_template.exists() and global_template.is_file():
                    logger.info(
                        f"Reading sbatch_template from {global_template}"
                    )
                    with open(global_template) as f:
                        self.sbatch_template_str = f.read()
                else:
                    logger.info(
                        "Could not find sbatcb_template at"
                        f" {local_template} or {global_template}"
                    )
                    logger.info("Using default template.")
                    self.sbatch_template_str = SBATCH_TEMPLATE
                    with open(global_template, "w") as f:
                        logger.info(
                            f"Creating new global template at {global_template}"
                        )
                        f.write(self.sbatch_template_str)
                logger.info(f"Creating new local template at {local_template}")
                with open(local_template, "w") as f:
                    f.write(self.sbatch_template_str)

        self.jinja_env = Environment(extensions=["jinja2.ext.do"])
        self.sbatch_template_ = self.jinja_env.from_string(
            self.sbatch_template_str
        )
        ast = self.jinja_env.parse(self.sbatch_template_str)
        self.sbatch_jinja_variables = meta.find_undeclared_variables(ast)  # type: ignore


@click.group(name="wandb-slurm")
@click.version_option(version=VERSION)
@click.option(
    "-e", "--entity", type=str, help="Wandb entity (username or team)"
)
@click.option(
    "-p",
    "--project",
    type=str,
    help="Wandb project",
)
@click.option(
    "-s",
    "--sweep",
    type=str,
    help="Wandb sweep (default:None)",
)
@click.option(
    "-d",
    "--directory",
    type=click.Path(path_type=pathlib.Path),
    default=pathlib.Path("slurm"),
    help="Directory to store slurm logs and scripts.",
)
@click.option(
    "-t",
    "--sbatch-template",
    type=click.Path(path_type=pathlib.Path),
    help="Path to jinja2 template file.",
)
@pass_context
@config_file_decorator()
def wandb_slurm(
    ctx: click.Context,
    entity: Optional[str],
    project: Optional[str],
    sweep: Optional[str],
    directory: pathlib.Path,
    sbatch_template: Optional[pathlib.Path],
) -> pd.DataFrame:
    ctx.obj = WandbUtilsSlurm(
        api=wandb.Api(),  # type: ignore
        entity=entity,
        project=project,
        sweep=sweep,
        directory=directory,
        sbatch_template=sbatch_template,
    )
    commands_config, global_config = load_config()
    ctx.default_map = commands_config.get("wandb-slurm", {})


@wandb_slurm.command("start-agents")
@click.option(
    "--inform-before-time",
    type=int,
    default=60,
    help="How many seconds before should the agents be informed before shutting them down?",
)
@click.option(
    "--signals",
    type=LIST,
    default=["TERM", "INT"],
    help="Signals to handle seperated buy '|' for example 'TERM|INT|CONT'  (default: 'TERM|INT').",
)
@click.option("--mem", type=str, default="12GB", help="#SBATCH --mem=")
@click.option(
    "--run-count",
    type=int,
    help="Runs per agent, ie `wandb agent --count <run-count> sweep_id`. (default: unlimited).",
)
@click.option(
    "--cpus-per-task", type=int, help="#SBATCH --cpus-per-task=", default=2
)
@click.option("--partition", type=str, help="#SBATCH --partition=")
@click.option("--num-gpus", type=int, help="#SBATCH --gres=gpu:")
@click.option("--num-agents", type=int, default=1)
@click.option(
    "--edit/--no-edit",
    is_flag=True,
    default=False,
    help="Edit final sbatch.sh",
)
@click.option(
    "--chain/--no-chain",
    is_flag=True,
    default=False,
    help="Insert dependencies between jobs by starting num-agents serially.",
)
@click.option(
    "--dependency",
    type=str,
    help=(
        """
Dependency types:

    after:jobid[:jobid...]	job can begin after the specified jobs have started

    afterany:jobid[:jobid...]	job can begin after the specified jobs have terminated

    afternotok:jobid[:jobid...]	job can begin after the specified jobs have failed

    afterok:jobid[:jobid...]	job can begin after the specified jobs have run to completion with an exit code of zero (see the user guide for caveats).

    singleton	jobs can begin execution after all previously launched jobs with the same name and user have ended. This is useful to collate results of a swarm or to send a notification at the end of a swarm.

        See `sbatch <https://slurm.schedmd.com/sbatch.html>`_ doc for details.
        """
    ),
)
@click.option(
    "--verbatim-args",
    type=LIST,
    default=[],
    help="arguments in kw=value seperated by | form to drop verbatim in sbatch.sh. For example 'exclude=node003,node004|account=abc",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Only create files and show command but do not submit jobs.",
)
@click.option(
    "--confirm",
    is_flag=True,
    default=False,
    help="Whether to ask for confirmation before submitting.",
)
@click.pass_obj
@config_file_decorator()
def start_agents_command(
    slurm: WandbUtilsSlurm,
    inform_before_time: int,
    signals: List[str],
    mem: str,
    run_count: Optional[int],
    cpus_per_task: int,
    partition: Optional[str],
    num_gpus: Optional[int],
    num_agents: int,
    edit: bool,
    chain: bool,
    dependency: Optional[str],
    verbatim_args: List,
    dry_run: bool,
    confirm: bool,
) -> None:
    assert slurm.sweep is not None, "wandb-utils --sweep has to be passed"
    job_dir = slurm.directory / slurm.sweep
    job_dir.mkdir(parents=True, exist_ok=True)
    dep_arg = dependency or ""
    sbatch_content = slurm.sbatch_template_.render(
        entity=slurm.entity,
        project=slurm.project,
        sweep=slurm.sweep,
        inform_before_time=inform_before_time,
        signals=signals,
        mem=mem,
        run_count=run_count,
        cpus_per_task=cpus_per_task,
        partition=partition,
        num_gpus=num_gpus,
        job_dir=job_dir,
        num_agents=num_agents if not chain else 1,
        chain=chain,
        verbatim_args=verbatim_args,
    )
    final_script = job_dir / "sbatch.sh"
    with open(final_script, "w") as f:
        logger.info(f"Writing final sbatch.sh to {final_script}")
        f.write(sbatch_content)

    if edit:
        os.system(f"vim {final_script}")

    with open(final_script) as f:
        sbatch_content = f.read()

    if not dry_run and confirm:
        y_n = input(
            "About to submit:\n{sbatch_content}\n\n Do you want to abort? [y/n] (n) "
        )

        if y_n not in ["y", "n", "", None]:
            raise ValueError("Please enter y or n.")

        if y_n == "y":
            logger.info("Aborting!")
            sys.exit(0)

    # submit job(s)

    if dry_run:
        logger.info("Not submitting job because --dry-run was set.")
        logger.info(
            " ".join(
                [
                    "Would have executed: ",
                    "sbatch",
                    "--dependency=dep_arg" if dep_arg else "",
                    f"{final_script}",
                ]
            )
        )
        logger.info(
            f"With the content in {final_script} as :\n{sbatch_content}"
        )
    else:
        logger.info("Submitting job(s)")

        for job_num in range(num_agents if chain else 1):
            dep = f"--dependency={dep_arg}" if dep_arg else ""
            sbatch_command = (
                ["sbatch"] + ([dep] if dep else []) + [str(final_script)]
            )
            try:
                submission = subprocess.run(
                    sbatch_command,
                    capture_output=True,
                )
                submission.check_returncode()
            except subprocess.CalledProcessError as pe:
                logger.error("Could not submit the job.")
                logger.error(f"stderr: {submission.stderr.decode('utf-8')}")
                logger.error(f"stdout: {submission.stderr.decode('utf-8')}")
                raise
            possible_jobid = submission.stdout.decode("utf-8").strip()
            # Expected str: Submitted .... <jobid>
            m = re.fullmatch(r"Submitted .+ (\d+)$", possible_jobid)

            if m:
                possible_jobid = m.groups()[0]
                logger.info(f"Submitted {possible_jobid}")
                dep_arg = f"afterany:{possible_jobid}"
            else:
                logger.error("Could not submit")
                logger.error(f"stderr: {submission.stderr.decode('utf-8')}")
                logger.error(f"stdout: {submission.stdout.decode('utf-8')}")
                raise RuntimeError
