"""
Visualizer-related Pydantic schemas
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    """Document response model"""
    id: int
    content: str
    metadata: Dict[str, Any]
    content_preview: str


class SearchResponse(BaseModel):
    """Search response model"""
    id: int
    content: str
    metadata: Dict[str, Any]
    similarity: float
    content_preview: str


class StatsResponse(BaseModel):
    """Database statistics response model"""
    total_chunks: int
    categories: Dict[str, int]
    files: Dict[str, int]
    avg_chunk_size: float
    metadata_keys: List[str]
