#!/usr/bin/env python3
"""
Database Initialization Entry Point - Main script for initializing the vector database

This script provides a command-line interface for initializing and setting up
the ChromaDB vector database for the RAG system.

Usage:
    python init_db.py
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.init_vectordb import main


if __name__ == "__main__":
    main()
