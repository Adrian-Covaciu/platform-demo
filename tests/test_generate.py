import pytest
from click.testing import CliRunner
from src.platform_generator.cli import generate

def test_retailers():
    runner = CliRunner()
    result = runner.invoke(generate)
    assert result.exit_code == 0


