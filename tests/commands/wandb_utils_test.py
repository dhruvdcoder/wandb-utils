from click.testing import CliRunner
from wandb_utils.commands import wandb_utils


def test_wandb_utils_help():
    runner = CliRunner()
    result = runner.invoke(wandb_utils, ["--help"])
    assert result.exit_code == 0
    result = runner.invoke(
        wandb_utils,
    )
    assert result.exit_code == 0
