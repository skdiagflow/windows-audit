"""Main entry point for running as a module."""
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .cli import main

if __name__ == "__main__":
    main()