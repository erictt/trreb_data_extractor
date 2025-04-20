#!/usr/bin/env python3
"""
Script to print help for all TRREB CLI commands.
"""

import sys
import subprocess
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from trreb.utils.logging import logger

commands = ["download", "extract", "process", "pipeline", "enrich"]

def main():
    """Print help for all CLI commands."""
    logger.info("Testing TRREB CLI help commands...\n")
    
    for cmd in commands:
        logger.info(f"\n{'='*80}")
        logger.info(f"Help for command: {cmd}")
        logger.info(f"{'='*80}")
        try:
            result = subprocess.run(
                ["python", "-m", "trreb.cli", cmd, "--help"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error: {e}")
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
