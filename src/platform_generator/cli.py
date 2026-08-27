import click
from .loader import load_retailers
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

cli.add_command(validate)