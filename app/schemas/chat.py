"""
Chat-related Pydantic schemas
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., min_length=1, max_length=1000, description="User message")


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    sources: List[Dict[str, Any]]
    confidence: float
    timestamp: str


class StatusResponse(BaseModel):
    """System status response model"""
    status: str
    documents: int
    chunks: int
    last_updated: str
    chroma_visualizer_enabled: bool
