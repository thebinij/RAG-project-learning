"""
FastAPI application definition
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import chat_router, visualizer_router, costs_router
from app.core.config import settings
from app.core.logging import console, logger

# Global service instances
_vector_service: Optional["VectorService"] = None
_chat_service: Optional["ChatService"] = None
_document_service: Optional["DocumentService"] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global _vector_service, _chat_service, _document_service

    # Startup
    console.print("\n" + "=" * 60, style="bold blue")
    console.print(
        "🚀 Starting LegendaryCorp AI Assistant (FastAPI)", style="bold green"
    )
    if settings.chroma_db_visualizer:
        console.print("   with ChromaDB Visualizer (ENABLED)", style="bold green")
    else:
        console.print("   ChromaDB Visualizer (DISABLED)", style="bold red")
    console.print("=" * 60, style="bold blue")

    logger.info("Initializing RAG components...")

    try:
        # Initialize services
        from app.services.chat_service import ChatService
        from app.services.document_service import DocumentService
        from app.services.vector_service import VectorService

        _vector_service = VectorService()
        logger.info("Vector service ready")

        _chat_service = ChatService(_vector_service)
        logger.info("Chat service ready")

        _document_service = DocumentService(_vector_service)
        logger.info("Document service ready")

        logger.info("All components ready!")

        # Initialize database with documents on first run
        if not _vector_service.is_initialized():
            logger.info("First run detected. Processing LegendaryCorp documents...")
            _document_service.process_all_documents()
            logger.info("Document processing complete!")

        yield

    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered RAG system with ChromaDB visualization",
    version=settings.app_version,
    lifespan=lifespan,
    redoc_url="/redoc" if settings.enable_redoc else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include API routers
app.include_router(chat_router, prefix="/api/v1")
app.include_router(costs_router, prefix="/api/v1")

# Visualizer router is excluded from API documentation
if settings.chroma_db_visualizer:
    # Mount visualizer router at /api/visualizer for API endpoints
    logger.info(f"Including visualizer router with prefix /api/visualizer")
    app.include_router(visualizer_router, prefix="/api/visualizer")
    logger.info(f"Visualizer router included successfully")
else:
    logger.warning("ChromaDB visualizer is disabled - visualizer router not included")


# ===== UTILITY FUNCTIONS =====


def get_vector_service():
    """Get vector service instance"""
    if _vector_service is None:
        raise HTTPException(status_code=503, detail="Vector service not initialized")
    return _vector_service


def get_chat_service():
    """Get chat service instance"""
    if _chat_service is None:
        raise HTTPException(status_code=503, detail="Chat service not initialized")
    return _chat_service


def get_document_service():
    """Get document service instance"""
    if _document_service is None:
        raise HTTPException(status_code=503, detail="Document service not initialized")
    return _document_service


# ===== MAIN ROUTES =====


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the chat interface"""
    return templates.TemplateResponse("chat/index.html", {"request": request})


@app.get("/chat")
async def chat_interface():
    """Redirect to chat interface"""
    return RedirectResponse(url="/")


@app.get("/help", response_class=HTMLResponse)
async def help_page(request: Request):
    """Help and documentation page"""
    return templates.TemplateResponse("help.html", {"request": request})


@app.get("/costs", response_class=HTMLResponse)
async def cost_dashboard(request: Request):
    """Cost analytics dashboard"""
    return templates.TemplateResponse("cost/index.html", {"request": request})


@app.post("/api/chat")
async def legacy_chat_redirect():
    """Redirect legacy /api/chat to /api/v1/chat for backward compatibility"""
    return RedirectResponse(url="/api/v1/chat", status_code=307)


@app.post("/api/chat/stream")
async def legacy_chat_stream_redirect():
    """Redirect legacy /api/chat/stream to /api/v1/chat/stream for backward compatibility"""
    return RedirectResponse(url="/api/v1/chat/stream", status_code=307)


# ===== VISUALIZER HTML ROUTES =====


@app.get("/visualizer", response_class=HTMLResponse, include_in_schema=False)
async def visualizer_dashboard(request: Request):
    """Main ChromaDB visualization dashboard"""
    try:
        vector_service = get_vector_service()
        stats = vector_service.get_stats()
        return templates.TemplateResponse(
            "visualizer/index.html", {"request": request, "stats": stats}
        )
    except Exception as e:
        logger.error(f"Visualizer dashboard error: {e}")
        return templates.TemplateResponse(
            "visualizer/index.html", {"request": request, "stats": {"error": str(e)}}
        )


@app.get("/visualizer/documents", response_class=HTMLResponse, include_in_schema=False)
async def visualizer_documents(request: Request):
    """Documents page for ChromaDB visualizer"""
    return templates.TemplateResponse("visualizer/documents.html", {"request": request})


@app.get("/visualizer/search", response_class=HTMLResponse, include_in_schema=False)
async def visualizer_search(request: Request):
    """Search page for ChromaDB visualizer"""
    return templates.TemplateResponse("visualizer/search.html", {"request": request})


@app.get("/visualizer/explore", response_class=HTMLResponse, include_in_schema=False)
async def visualizer_explore(request: Request):
    """Explore page for ChromaDB visualizer"""
    return templates.TemplateResponse("visualizer/explore.html", {"request": request})


# ===== HEALTH CHECK =====


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from datetime import datetime

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "vector_service": _vector_service is not None,
            "chat_service": _chat_service is not None,
            "document_service": _document_service is not None,
        },
    }


@app.get("/api/status")
async def api_status():
    """API status endpoint for frontend compatibility"""
    try:
        vector_service = get_vector_service()
        stats = vector_service.get_stats()
        return {
            "status": "operational",
            "documents": stats["total_documents"],
            "chunks": stats["total_chunks"],
            "last_updated": stats["last_updated"],
            "chroma_visualizer_enabled": settings.chroma_db_visualizer,
        }
    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== ERROR HANDLERS =====


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    return HTMLResponse(
        content="<h1>404 - Page Not Found</h1><p>The requested page could not be found.</p>",
        status_code=404,
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {exc}")
    return HTMLResponse(
        content="<h1>500 - Internal Server Error</h1><p>Something went wrong on our end.</p>",
        status_code=500,
    )
