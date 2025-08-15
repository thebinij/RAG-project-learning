#!/usr/bin/env python3
"""
Database Initialization - Sets up ChromaDB for the RAG system

This script provides a command-line interface for initializing and setting up
the ChromaDB vector database for the RAG system.

Usage:
    python init_db.py                    # Check database status
    python init_db.py --force            # Force clear and reinitialize
    python init_db.py -f                 # Short form for force
    python init_db.py --status           # Show database status only
"""

import os
import sys
import argparse
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.engines.vector_engine import VectorEngine
from app.core.config import settings
from app.core.logging import logger


def main():
    """Initialize the vector database"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="LegendaryCorp Vector Database Initialization")
    parser.add_argument("--force", "-f", action="store_true", help="Force clear and reinitialize database")
    parser.add_argument("--status", "-s", action="store_true", help="Show database status only")
    args = parser.parse_args()
    
    print("🚀 LegendaryCorp Vector Database Initialization")
    print("=" * 50)
    
    try:
        # Initialize vector engine
        print("🔌 Connecting to ChromaDB...")
        vector_engine = VectorEngine()
        
        # Check if collection exists
        if vector_engine.is_initialized():
            print("✅ Database already initialized")
            print(f"📊 Collection: {vector_engine.collection.name}")
            print(f"📈 Document count: {vector_engine.collection.count()}")
            
            if args.force:
                print("\n🗑️  Force clearing database...")
                confirm = input("⚠️  This will delete ALL documents. Are you sure? (yes/no): ")
                if confirm.lower() in ['yes', 'y']:
                    vector_engine.clear_collection()
                    print("✅ Database cleared and reinitialized successfully")
                else:
                    print("❌ Database clearing cancelled")
                    return
            elif args.status:
                print("\n📊 Database Status:")
                print(f"   Collection: {vector_engine.collection.name}")
                print(f"   Document Count: {vector_engine.collection.count()}")
                print(f"   Last Updated: {vector_engine.last_updated}")
                return
        else:
            print("🆕 Initializing new database...")
            vector_engine.clear_collection()
            print("✅ Database initialized successfully")
        
        if not args.status:
            print("\n🎯 Database ready for RAG operations!")
            print("💡 Next step: Run 'python ingest_docs.py' to add documents")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
