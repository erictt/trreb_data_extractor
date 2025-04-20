"""
Command modules for TRREB data extractor CLI.
Each module contains a specific command implementation.
"""

from trreb.cli.commands.fetch import fetch
from trreb.cli.commands.process import process
from trreb.cli.commands.economy import economy

__all__ = ["fetch", "process", "economy"]
