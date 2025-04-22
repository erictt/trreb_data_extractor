"""
CLI command group for TRREB data extractor.
"""

import click

from trreb.cli.commands.convert import convert
from trreb.cli.commands.economy import economy  
from trreb.cli.commands.fetch import fetch
from trreb.cli.commands.forecast import forecast
from trreb.cli.commands.normalize import normalize

@click.group()
def cli():
    """TRREB data extractor command line interface."""
    pass

# Register commands
cli.add_command(convert)
cli.add_command(economy)
cli.add_command(fetch)
cli.add_command(forecast)
cli.add_command(normalize)
