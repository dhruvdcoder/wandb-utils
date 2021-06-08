#!/usr/bin/env python
# see: https://pypi.org/project/jinja2-ansible-filters/ to convert this to use jinja
import argparse
import os
from pathlib import Path


def main(args):
    slurm_dir = Path(args.slurm_dir)
    slurm_dir.mkdir(parents=True, exist_ok=True)
    slurm_gitignore = Path(slurm_dir / ".gitignore")

    if not slurm_gitignore.exists():
        with open(slurm_gitignore, "w") as f:
            f.write("*")

    template_path = dict()
    template_path["srun.sh"] = Path(slurm_dir / args.srun_template)
    template_path["sbatch.sh"] = Path(slurm_dir / args.sbatch_template)

    template_str = dict()
    template_str["srun.sh"] = "\n".join(
        (
            "#!/bin/sh",
            "module load cuda/10.0.130",
        )
    )
    template_str["sbatch.sh"] = "\n".join(
        (
            "#!/bin/bash",
            "#SBATCH --gres=gpu:1",
            "#SBATCH --partition=gpu",
            "#SBATCH --cpus-per-task=2",
            "#SBATCH --mem=16GB",
        )
    )

    for fname in ["srun.sh", "sbatch.sh"]:
        if not template_path[fname].exists():
            with open(template_path[fname], "w") as f:
                f.write(template_str[fname])
        os.system(f"chmod +x {template_path[fname]}")

    job_dir = Path(slurm_dir / args.sweep_id)
    try:
        job_dir.mkdir(parents=True, exist_ok=False)
    except OSError as e:
        if not args.force:
            raise ValueError(
                f"Got sweep_id = {args.sweep_id}, but directory {job_dir} already exists!"
            )

    file_path = dict()
    file_path["srun.sh"] = Path(job_dir / args.srun_filename)
    file_path["sbatch.sh"] = Path(job_dir / args.sbatch_filename)

    # The following might be nice but are definitely not necessary:
    # TODO: Allow SBATCH defaults to be overridden by pass-through arguments to this script

    file_str = dict()
    complete_sweep_id_entires = []

    if args.wandb_entity:
        complete_sweep_id_entires.append(args.wandb_entity)

    if args.wandb_project:
        complete_sweep_id_entires.append(args.wandb_project)
    complete_sweep_id_entires.append(args.sweep_id)
    complete_sweep_id = "/".join(complete_sweep_id_entires)
    file_str["srun.sh"] = "\n".join(
        (
            "",
            f"wandb agent --count 20 {complete_sweep_id}",
            # f"pwd", # for testing
            # f"./test.sh", # for testing
        )
    )

    file_str["sbatch.sh"] = "\n".join(
        (
            "",
            f"#SBATCH --job-name={args.sweep_id}",
            f"#SBATCH --output={job_dir}/%A-%a.out",
            # f"#SBATCH --error={job_dir}/%A-%a.error",
            f"#SBATCH --ntasks={args.num_agents_per_job}",
            f"#SBATCH --array=1-{args.num_jobs}\n"
            if args.num_jobs > 1
            else "",
            f"srun {file_path['srun.sh']}",
        )
    )

    for fname in ["srun.sh", "sbatch.sh"]:
        os.system(f"cp {template_path[fname]} {file_path[fname]}")
        with open(file_path[fname], "a") as f:
            f.write(file_str[fname])

    if args.edit_srun:
        os.system(f"{args.editor} {file_path['srun.sh']}")

    if args.edit_sbatch:
        os.system(f"{args.editor} {file_path['sbatch.sh']}")

    if not args.no_run:
        os.system(f"sbatch {file_path['sbatch.sh']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run multiple wandb agents via SLURM"
    )
    parser.add_argument("sweep_id", type=str)
    parser.add_argument(
        "-e",
        "--wandb-entity",
        type=str,
        help="your wandb username or team name",
    )
    parser.add_argument(
        "-p",
        "--wandb-project",
        type=str,
        help="your wandb project for this sweep.",
    )
    parser.add_argument("--num-jobs", type=int, default=1)
    parser.add_argument("--num-agents-per-job", type=int, default=1)
    parser.add_argument(
        "--edit-sbatch",
        action="store_true",
        help="open the sbatch.sh file in a text editor before running",
    )
    parser.add_argument(
        "--edit-srun",
        action="store_true",
        help="open the srun.sh file in a text editor before running",
    )
    parser.add_argument(
        "--no-run",
        action="store_true",
        help="don't run the job(s), just create the sh files",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="force creation of job folder if it already exists, potentially overwriting data",
    )
    parser.add_argument(
        "--slurm_dir",
        type=str,
        default="slurm",
        help="directory to store slurm files in",
    )
    parser.add_argument(
        "--srun-filename",
        type=str,
        default="srun.sh",
        help="filename of srun script (to be created)",
    )
    parser.add_argument(
        "--sbatch-filename",
        type=str,
        default="sbatch.sh",
        help="filename of sbatch script (to be created)",
    )
    parser.add_argument(
        "--srun-template",
        type=str,
        default="srun.sh",
        help="filename of srun template (which will be copied and appended to) relative to SLURM_DIR",
    )
    parser.add_argument(
        "--sbatch-template",
        type=str,
        default="sbatch.sh",
        help="filename of sbatch template (which will be copied and appended to) relative to SLURM_DIR",
    )
    parser.add_argument("--editor", type=str, default="vim")
    # More generally, should be able to use EDITOR = "${EDITOR:-vim}" but I don't always have my editor set.

    args = parser.parse_args()
    main(args)
