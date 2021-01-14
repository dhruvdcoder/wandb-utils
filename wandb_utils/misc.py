from typing import List, Tuple, Union, Dict, Any, Optional
import wandb
import pandas as pd
import logging
from pathlib import Path
from jinja2 import Template
import tempfile
import shutil
import subprocess
import json
import re
import copy

logger = logging.getLogger(__name__)


def all_data_df(
    entity: str,
    project: str,
    sweep: Optional[str] = None,
    api: Optional[wandb.apis.public.Api] = None,
) -> pd.DataFrame:
    """
    Get the data for all the runs.
    """

    if api is None:
        logger.info(f"Creating api instance")
        api = wandb.Api({"entity": entity, "project": project})
    logger.info(f"Querying wandb...")

    if sweep is None:  # get all runs
        runs = api.runs(f"{entity}/{project}")
    else:
        runs = api.sweep(f"{entity}/{project}/{sweep}").runs
    summary_list = []
    config_list = []
    name_list = []
    sweep_list = []

    for run in runs:
        # run.summary are the output key/values like accuracy.  We call ._json_dict to omit large files
        summary_list.append(run.summary._json_dict)

        # run.config is the input metrics.  We remove special values that start with _.
        config_list.append(
            {k: v for k, v in run.config.items() if not k.startswith("_")}
        )

        # run.name is the name of the run.
        name_list.append(run.id)

        # sweep
        sweep_list.append(run.sweep.id if run.sweep else "")

    summary_df = pd.DataFrame.from_records(summary_list)
    config_df = pd.DataFrame.from_records(config_list)
    name_df = pd.DataFrame({"run": name_list})
    sweep_df = pd.DataFrame({"sweep": sweep_list})
    all_df = pd.concat([name_df, sweep_df, config_df, summary_df], axis=1)

    return all_df


def find_best_models_in_sweeps(
    entity: str,
    project: str,
    metric: str,
    maximum: bool = True,
    sweep: Optional[str] = None,
    api: Optional[wandb.apis.public.Api] = None,
) -> pd.DataFrame:
    all_df = all_data_df(entity, project, sweep=sweep, api=api)
    # ref: https://stackoverflow.com/questions/32459325/python-pandas-dataframe-select-row-by-max-value-in-group

    if maximum:
        return all_df.loc[
            all_df.groupby("sweep", dropna=True)[metric].idxmax()
        ]
    else:
        return all_df.loc[
            all_df.groupby("sweep", dropna=True)[metric].idxmin()
        ]


def get_config_file_for_run(
    entity: str,
    project: str,
    run_id: str,
    relative_path: str = "training_dumps/config.json",
    output_path: str = "config.json",
    api: Optional[wandb.apis.public.Api] = None,
) -> wandb.apis.public.Api:
    if api is None:
        logger.info(f"Creating api instance")
        api = wandb.Api()

    run = api.run(f"{entity}/{project}/{run_id}")
    logger.info(f"Getting config for {entity}/{project}/{run_id}")
    with tempfile.TemporaryDirectory() as dir_:
        temp_file = run.file(relative_path).download(dir_)
        temp_file_path = Path(temp_file.name)
        logger.info(
            f"Downloaded {entity}/{project}/{run_id}/{relative_path} to {temp_file_path}"
        )
        temp_file.close()
        output_path = Path(output_path)

        if output_path.suffix not in [".json", ".jsonnet"]:
            logger.warning(f"{output_path.name} not JSON or JSONNET.")

        if not output_path.parent.exists():
            logger.info(f"Creating dir {output_path.parent}")
            output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(temp_file_path, output_path)
        logger.info(f"Moved the file to {output_path}")

        return api


def get_config_file_for_best_run(
    entity: str,
    project: str,
    sweep_id: str,
    metric: str,
    maximum: bool = True,
    relative_path: str = "training_dumps/config.json",
    output_path: str = "config.json",
    api: Optional[wandb.apis.public.Api] = None,
) -> str:
    all_sweeps_best = find_best_models_in_sweeps(
        entity, project, metric, sweep=sweep_id, api=api
    )
    run_id = all_sweeps_best[all_sweeps_best["sweep"] == sweep_id][
        "run"
    ].values[0]
    get_config_file_for_run(
        entity, project, run_id, output_path=output_path, api=api
    )

    return run_id


multiple_runs_sweep = Template(
    """
command:
- ${program}
- --subcommand="{{subcommand or 'train'}}"
{% for package in include_packages -%}
- --include-package={{package}}
{% endfor -%}
- --config_file={{config_file_path}}
- --wandb_tags={{wandb_tags|join(',')}}
- ${args}

method: grid
metric:
  goal: maximize
  name: best_validation_MAP

name: {{sweep_name}}

parameters:
  {{seed_parameter}}:
    values:
    - 2
    - 123
    - 234
    - 579
    - 9099
    - 23
    - 456
    - 9897
    - 5
    - 10
program: {{program or 'wandb_allennlp'}}
"""
)


jsonnet_with_seed_template = Template(
    """
local seed = std.parseJson(std.extVar('seed'));

"""
)


def with_fallback(
    preferred: Dict[str, Any], fallback: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Deep merge two dicts, preferring values from `preferred`.
    Ref: allennlp/common/params.py
    """

    def merge(preferred_value: Any, fallback_value: Any) -> Any:
        if isinstance(preferred_value, dict) and isinstance(
            fallback_value, dict
        ):
            return with_fallback(preferred_value, fallback_value)
        elif isinstance(preferred_value, dict) and isinstance(
            fallback_value, list
        ):
            # treat preferred_value as a sparse list, where each key is an index to be overridden
            merged_list = fallback_value

            for elem_key, preferred_element in preferred_value.items():
                try:
                    index = int(elem_key)
                    merged_list[index] = merge(
                        preferred_element, fallback_value[index]
                    )
                except ValueError:
                    raise ConfigurationError(
                        "could not merge dicts - the preferred dict contains "
                        f"invalid keys (key {elem_key} is not a valid list index)"
                    )
                except IndexError:
                    raise ConfigurationError(
                        "could not merge dicts - the preferred dict contains "
                        f"invalid keys (key {index} is out of bounds)"
                    )

            return merged_list
        else:
            return copy.deepcopy(preferred_value)

    preferred_keys = set(preferred.keys())
    fallback_keys = set(fallback.keys())
    common_keys = preferred_keys & fallback_keys

    merged: Dict[str, Any] = {}

    for key in preferred_keys - fallback_keys:
        merged[key] = copy.deepcopy(preferred[key])

    for key in fallback_keys - preferred_keys:
        merged[key] = copy.deepcopy(fallback[key])

    for key in common_keys:
        preferred_value = preferred[key]
        fallback_value = fallback[key]

        merged[key] = merge(preferred_value, fallback_value)

    return merged


def create_multiple_run_sweep_for_run(
    entity: str,
    project: str,
    run: Optional[str] = None,
    sweep: Optional[str] = None,
    metric: Optional[str] = None,
    maximum: bool = True,
    relative_path: str = "training_dumps/config.json",
    output_path: str = "config.json",
    seed_parameters: Optional[List[str]] = None,
    api: Optional[wandb.apis.public.Api] = None,
    **sweep_args,
):
    """
    Example::

        create_multiple_run_sweep_for_run('iesl-boxes','multilabel-learning-datasets',
                                  run='nyre9qr5',
                                  sweep_args=dict(include_packages=['multilabel_learning'],
                                                  sweep_name='test_sweep',
                                                  wandb_tags=['test', 'dryrun'],
                                                  fixed_overrides='{"type": "train_test_log_to_wandb"}'
                                                 )
                                 )

    """
    output_path = Path(output_path)

    if run:
        get_config_file_for_run(
            entity,
            project,
            run,
            relative_path=relative_path,
            output_path=output_path,
            api=api,
        )
    elif sweep and metric:
        run = get_config_file_for_best_run(
            entity,
            project,
            sweep,
            metric=metric,
            relative_path=relative_path,
            output_path=output_path,
            api=api,
        )
    else:
        raise ValueError(
            f"Either run or (sweep and metric) have to be supplied."
        )

    with open(output_path, "r") as f:
        config = json.load(f)

    if sweep_args.get("fixed_overrides"):
        overrides = json.loads(sweep_args.pop("fixed_overrides"))
        config = with_fallback(preferred=overrides, fallback=config)
    # add seed parameters

    if seed_parameters:
        placeholder = "__temp__seed__"

        for param in seed_parameters:
            config[param] = placeholder
        config_str = (
            "local seed = std.parseJson(std.extVar('seed'));\n"
            + json.dumps(config)
        )
        regex = r"\"__temp__seed__\""
        config_str = re.sub(
            regex,
            "seed",
            config_str,
            len(seed_parameters),
            re.MULTILINE,
        )

        if output_path.suffix != ".jsonnet":
            output_path = output_path.with_suffix(".jsonnet")
        logger.info(
            f"Added seed parameters and writing final config to {output_path}"
        )
        with open(output_path, "w") as f:
            f.write(config_str)

    tags = sweep_args.get("wandb_tags", []) or []
    tags += ["multiple_runs", run]
    sweep_args["wandb_tags"] = tags

    if api is None:
        api = wandb.Api()
        sweep_args["wandb_tags"] += api.run(f"{entity}/{project}/{run}").tags
    with tempfile.TemporaryDirectory() as dir_:
        sweep_file = Path(dir_) / f"{run}_sweep.yaml"
        logger.info(f"Generated sweep config {sweep_file}")
        with open(sweep_file, "w") as f:
            multiple_runs_sweep.stream(
                **sweep_args,
                config_file_path=str(output_path.absolute()),
                seed_parameter="env.seed"
                if seed_parameters
                else "pytorch_seed",
            ).dump(f)

        create_sweep = subprocess.run(
            ["wandb", "sweep", "-e", entity, "-p", project, sweep_file],
            text=True,
        )

        if create_sweep.returncode != 0:
            logger.error(f"{create_sweep.stderr}")
            raise RuntimeError("Error creating sweep")
        else:
            logger.info("Created sweep on the server.")
