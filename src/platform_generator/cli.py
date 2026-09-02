import click
from .loader import load_retailers
from .generator import generate_retailer
import sys

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

cli.add_command(validate)
cli.add_command(generate)