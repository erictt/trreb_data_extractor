"""
Command modules for TRREB data extractor CLI.
Each module contains a specific command implementation.
"""

from trreb.cli.commands.fetch import fetch
from trreb.cli.commands.economy import economy
from trreb.cli.commands.convert import convert
from trreb.cli.commands.normalize import normalize
from trreb.cli.commands.forecast import forecast

__all__ = ["fetch", "economy", "convert", "normalize", "forecast"]
