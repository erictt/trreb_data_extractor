#!/usr/bin/env python3
"""
Script to print help for all TRREB CLI commands.
"""

import sys
import subprocess
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

commands = ["download", "extract", "process", "pipeline", "enrich"]

def main():
    """Print help for all CLI commands."""
    print("Testing TRREB CLI help commands...\n")
    
    for cmd in commands:
        print(f"\n{'='*80}")
        print(f"Help for command: {cmd}")
        print(f"{'='*80}")
        try:
            result = subprocess.run(
                ["python", "-m", "trreb.cli", cmd, "--help"],
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            print(f"Stdout: {e.stdout}")
            print(f"Stderr: {e.stderr}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
