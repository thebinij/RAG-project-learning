"""
Chat service for RAG operations
"""

from typing import List, Dict, Any
from app.core.logging import logger
from app.core.config import settings
import sys
import os

from app.core.engines.chat_engine import ChatEngine


class ChatService:
    """Service layer for chat and RAG operations"""
    
    def __init__(self, vector_service):
        """Initialize the chat service"""
        logger.info("Initializing ChatService...")
        
        self.vector_service = vector_service
        self.chat_engine = ChatEngine(vector_service.vector_engine)
        logger.info("ChatService initialized successfully")
    
    def get_response(self, user_query: str) -> Dict[str, Any]:
        """Get chat response from RAG system"""
        return self.chat_engine.get_response(user_query)
    
    def get_system_prompt(self) -> str:
        """Get the system prompt"""
        return self.chat_engine.system_prompt
