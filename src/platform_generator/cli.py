import click
from .loader import load_retailers
from .generator import generate_retailer
import difflib
import sys
import tempfile
from pathlib import Path

@click.group()
def cli():
    pass

@click.command()
def validate():
    try:
        list(load_retailers())
        click.echo("Registry OK")
    except Exception as e:
        print(e)
        sys.exit(1)

@click.command()
@click.option("--retailer", default=None)
def generate(retailer):
    retailers = list(load_retailers())
    if retailer is not None:
        retailers = [r for r in retailers if r.name == retailer]
        if not retailers:
            raise click.ClickException(f"No such retailer: {retailer}")
    for var in retailers:
        generate_retailer(var)
    click.echo("Generated")

@click.command()
@click.option("--retailer", default=None)
def diff(retailer):
    retailers = list(load_retailers())
    if retailer is not None:
        retailers = [r for r in retailers if r.name == retailer]
        if not retailers:
            raise click.ClickException(f"No such retailer: {retailer}")

    has_diff = False
    for r in retailers:
        with tempfile.TemporaryDirectory() as tmp:
            generate_retailer(r, outdir=f"{tmp}/{r.name}")
            for service in r.services:
                generated = Path(tmp) / r.name / f"{service.name}.yaml"
                committed = Path("rendered/k8s") / r.name / f"{service.name}.yaml"
                before = committed.read_text() if committed.exists() else ""
                after = generated.read_text() if generated.exists() else ""
                text = "".join(difflib.unified_diff(
                    before.splitlines(keepends=True),
                    after.splitlines(keepends=True),
                    fromfile="committed",
                    tofile="generated",
                ))
                if text:
                    has_diff = True
                    click.echo(text)
    if has_diff:
        sys.exit(1)

cli.add_command(validate)
cli.add_command(generate)
cli.add_command(diff)