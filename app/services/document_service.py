"""
Document service for document processing operations
"""

from typing import List, Dict, Any
from app.core.logging import logger
from app.core.config import settings
import sys
import os

from app.core.engines.document_processor import DocumentProcessor


class DocumentService:
    """Service layer for document processing operations"""
    
    def __init__(self, vector_service):
        """Initialize the document service"""
        logger.info("Initializing DocumentService...")
        
        self.vector_service = vector_service
        self.doc_processor = DocumentProcessor(vector_service.vector_engine)
        logger.info("DocumentService initialized successfully")
    
    def process_all_documents(self):
        """Process all documents in the knowledge-docs directory"""
        return self.doc_processor.process_all_documents()
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get document processing status"""
        # This would be implemented based on your needs
        return {"status": "ready"}
