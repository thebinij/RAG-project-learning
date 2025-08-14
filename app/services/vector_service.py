"""
Vector service for ChromaDB operations
"""

from typing import List, Dict, Any, Optional
from app.core.logging import logger
from app.core.config import settings
import sys
import os

from app.core.engines.vector_engine import VectorEngine


class VectorService:
    """Service layer for vector database operations"""
    
    def __init__(self):
        """Initialize the vector service"""
        logger.info("Initializing VectorService...")
        
        # Set environment variables
        os.environ['TOKENIZERS_PARALLELISM'] = settings.tokenizers_parallelism
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = settings.hf_hub_disable_telemetry
        os.environ['TRANSFORMERS_OFFLINE'] = settings.transformers_offline
        
        self.vector_engine = VectorEngine()
        logger.info("VectorService initialized successfully")
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        return self.vector_engine.search(query, limit)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        return self.vector_engine.get_stats()
    
    def is_initialized(self) -> bool:
        """Check if the vector database is initialized"""
        return self.vector_engine.is_initialized()
    
    def get_client(self):
        """Get the ChromaDB client"""
        return self.vector_engine.client
    
    def get_collection(self):
        """Get the ChromaDB collection"""
        return self.vector_engine.collection
