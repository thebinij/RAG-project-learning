"""
Chat API router
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest, ChatResponse, StatusResponse
from app.services.chat_service import ChatService
from app.services.vector_service import VectorService
from app.core.logging import logger

chat_router = APIRouter(prefix="/chat", tags=["Chat API"])


async def get_chat_service() -> ChatService:
    """Dependency to get chat service"""
    from app.app import get_chat_service as get_service

    return get_service()


async def get_vector_service() -> VectorService:
    """Dependency to get vector service"""
    from app.app import get_vector_service as get_service

    return get_service()


@chat_router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest, chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a chat message and get an AI response.

    This endpoint processes user messages through the RAG system and returns
    contextual responses based on the LegendaryCorp knowledge base.
    """
    try:
        # Get response from RAG system
        response = chat_service.get_response(request.message)

        return ChatResponse(
            response=response["answer"],
            sources=response["sources"],
            confidence=response["confidence"],
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def generate_stream_response(message: str, chat_service: ChatService):
    """Generate streaming response"""
    try:
        # Send initial event
        yield f"data: {json.dumps({'event': 'start'})}\n\n"

        # Get response from RAG system
        response = chat_service.get_response(message)

        # Stream the response character by character to preserve markdown formatting
        response_text = response["answer"]
        for char in response_text:
            await asyncio.sleep(0.01)  # Async delay for streaming effect
            yield f"data: {json.dumps({'event': 'token', 'content': char})}\n\n"

        # Send sources at the end
        yield f"data: {json.dumps({'event': 'sources', 'sources': response['sources'], 'confidence': response['confidence']})}\n\n"

        # Send completion event
        yield f"data: {json.dumps({'event': 'done'})}\n\n"

    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f"data: {json.dumps({'event': 'error', 'error': str(e)})}\n\n"


@chat_router.post("/stream")
async def chat_stream(
    request: ChatRequest, chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a chat message and get a streaming AI response.

    This endpoint provides real-time streaming responses for a more interactive
    chat experience. Responses are streamed character by character to preserve
    markdown formatting.
    """
    return StreamingResponse(
        generate_stream_response(request.message, chat_service),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@chat_router.get("/status", response_model=StatusResponse)
async def status(vector_service: VectorService = Depends(get_vector_service)):
    """
    Get the current system status and statistics.

    Returns information about the vector database, including document counts,
    chunk counts, and last update timestamps.
    """
    try:
        stats = vector_service.get_stats()
        return StatusResponse(
            status="operational",
            documents=stats["total_documents"],
            chunks=stats["total_chunks"],
            last_updated=stats["last_updated"],
            chroma_visualizer_enabled=True,  # This should come from config
        )
    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
