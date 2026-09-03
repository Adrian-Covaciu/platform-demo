from pathlib import Path

from click.testing import CliRunner

from src.platform_generator.cli import diff

COMPONENT_PATH = Path("registry/services/web/http/component.yaml")


def test_diff_in_sync_shows_no_changes():
    # Assumes rendered/ is committed and up to date with the registry, as
    # it should be right after a `platform generate`.
    runner = CliRunner()
    result = runner.invoke(diff)
    assert result.exit_code == 0
    assert result.output == ""


def test_diff_shows_edited_component():
    original = COMPONENT_PATH.read_text()
    try:
        COMPONENT_PATH.write_text(original.rstrip("\n") + "\nreplicas: 3\n")
        runner = CliRunner()
        result = runner.invoke(diff, ["--retailer", "acme"])
        assert result.exit_code != 0
        assert "-  replicas: 1" in result.output
        assert "+  replicas: 3" in result.output
    finally:
        COMPONENT_PATH.write_text(original)


def test_diff_unknown_retailer_fails():
    runner = CliRunner()
    result = runner.invoke(diff, ["--retailer", "does-not-exist"])
    assert result.exit_code != 0
