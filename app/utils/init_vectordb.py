"""
Database Initialization Utility - Sets up ChromaDB for the RAG system

This utility handles the initialization of the ChromaDB vector database,
including collection creation and basic setup.
"""

import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.engines.vector_engine import VectorEngine
from app.core.config import settings
from app.core.logging import logger


def main():
    """Initialize the vector database"""
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
        else:
            print("🆕 Initializing new database...")
            vector_engine.clear_collection()
            print("✅ Database initialized successfully")
        
        print("\n🎯 Database ready for RAG operations!")
        print("💡 Next step: Run 'python ingest_docs.py' to add documents")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
