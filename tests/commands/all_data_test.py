from click.testing import CliRunner
from wandb_utils.commands import wandb_utils


def test_all_data_help():
    runner = CliRunner()
    result = runner.invoke(wandb_utils, "all-data --help")
    assert result.exit_code == 0


def test_all_data_with_field_filter():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        wandb_utils,
        "-e dhruveshpate -p wandb-utils-tester all-data -f best_validation_MAP -f best_validation_micro_map print",
    )
    assert result.exit_code == 0
