"""Application entry point and development server."""
import os
import sys

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import run_server

if __name__ == "__main__":
    run_server()