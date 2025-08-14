"""
ChromaDB Visualizer API routes
"""

from collections import Counter
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.logging import logger
from app.services.vector_service import VectorService

# Create router
visualizer_router = APIRouter(tags=["ChromaDB Visualizer"], include_in_schema=False)


async def get_vector_service() -> VectorService:
    """Dependency to get vector service"""
    from app.app import get_vector_service as get_service

    return get_service()


class ChromaDBWebViewer:
    def __init__(self, vector_service: VectorService):
        """Initialize the web viewer using existing VectorService's ChromaDB client"""
        try:
            # Use the existing ChromaDB client from VectorService
            self.client = vector_service.get_client()
            self.collection = vector_service.get_collection()
            logger.info("ChromaDB viewer ready (using existing client)")
        except Exception as e:
            logger.warning(f"ChromaDB viewer initialization failed: {e}")
            self.client = None
            self.collection = None

    def get_database_stats(self):
        """Get comprehensive database statistics"""
        try:
            if not self.collection:
                return {"error": "ChromaDB not available"}

            total_chunks = self.collection.count()

            if total_chunks == 0:
                return {
                    "total_chunks": 0,
                    "categories": {},
                    "files": {},
                    "avg_chunk_size": 0,
                    "metadata_keys": [],
                }

            # Get all documents with metadata
            all_docs = self.collection.get(include=["metadatas", "documents"])

            # Category distribution
            categories = [
                meta.get("category", "Unknown") for meta in all_docs["metadatas"]
            ]
            category_counts = Counter(categories)

            # File distribution
            files = [meta.get("file", "Unknown") for meta in all_docs["metadatas"]]
            file_counts = Counter(files)

            # Average chunk size
            chunk_lengths = [len(doc) for doc in all_docs["documents"]]
            avg_chunk_size = (
                sum(chunk_lengths) / len(chunk_lengths) if chunk_lengths else 0
            )

            # Metadata keys
            metadata_keys = (
                list(all_docs["metadatas"][0].keys()) if all_docs["metadatas"] else []
            )

            return {
                "total_chunks": total_chunks,
                "categories": dict(category_counts),
                "files": dict(file_counts),
                "avg_chunk_size": round(avg_chunk_size, 1),
                "metadata_keys": metadata_keys,
            }
        except Exception as e:
            return {"error": str(e)}

    def search_documents(self, query, limit=10):
        """Search for documents using semantic search"""
        try:
            if not self.collection:
                return {"error": "ChromaDB not available"}

            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                include=["documents", "metadatas", "distances"],
            )

            if results["metadatas"] and len(results["metadatas"][0]) > 0:
                search_results = []
                for i, (doc, meta, distance) in enumerate(
                    zip(
                        results["documents"][0],
                        results["metadatas"][0],
                        results["distances"][0],
                    )
                ):
                    similarity = 1 - distance
                    search_results.append(
                        {
                            "id": i,
                            "content": doc,
                            "metadata": meta,
                            "similarity": round(similarity, 3),
                            "content_preview": (
                                doc[:200] + "..." if len(doc) > 200 else doc
                            ),
                        }
                    )
                return search_results
            else:
                return []
        except Exception as e:
            return {"error": str(e)}

    def get_all_documents(self, limit=None, offset=0):
        """Get all documents with pagination"""
        try:
            if not self.collection:
                return {"error": "ChromaDB not available"}

            all_docs = self.collection.get(include=["metadatas", "documents"])

            if not all_docs["metadatas"]:
                return []

            documents = []
            for i, (meta, doc) in enumerate(
                zip(all_docs["metadatas"], all_docs["documents"])
            ):
                if limit and i >= limit:
                    break
                if i < offset:
                    continue

                documents.append(
                    {
                        "id": i,
                        "content": doc,
                        "metadata": meta,
                        "content_preview": doc[:150] + "..." if len(doc) > 150 else doc,
                    }
                )

            return documents
        except Exception as e:
            return {"error": str(e)}

    def get_documents_by_category(self, category):
        """Get documents filtered by category"""
        try:
            if not self.collection:
                return {"error": "ChromaDB not available"}

            all_docs = self.collection.get(include=["metadatas", "documents"])

            if not all_docs["metadatas"]:
                return []

            documents = []
            for i, (meta, doc) in enumerate(
                zip(all_docs["metadatas"], all_docs["documents"])
            ):
                if meta.get("category") == category:
                    documents.append(
                        {
                            "id": i,
                            "content": doc,
                            "metadata": meta,
                            "content_preview": (
                                doc[:150] + "..." if len(doc) > 150 else doc
                            ),
                        }
                    )

            return documents
        except Exception as e:
            return {"error": str(e)}


# Note: HTML routes are now handled by the main app
# This router only handles API endpoints


# ===== API ENDPOINTS =====


@visualizer_router.get("/stats")
async def api_visualizer_stats(
    vector_service: VectorService = Depends(get_vector_service),
):
    """
    Get comprehensive ChromaDB database statistics.

    Returns detailed information about the vector database including:
    - Total chunks and documents
    - Category distribution
    - File distribution
    - Average chunk sizes
    - Available metadata keys
    """
    viewer = ChromaDBWebViewer(vector_service)
    stats = viewer.get_database_stats()
    return stats


@visualizer_router.get("/search")
async def api_visualizer_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Number of results"),
    vector_service: VectorService = Depends(get_vector_service),
):
    """API endpoint for document search in ChromaDB"""
    if not q:
        return []

    viewer = ChromaDBWebViewer(vector_service)
    results = viewer.search_documents(q, limit)
    return results


@visualizer_router.get("/documents")
async def api_visualizer_documents(
    limit: Optional[int] = Query(
        None, ge=1, le=1000, description="Number of documents"
    ),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    category: Optional[str] = Query(None, description="Filter by category"),
    vector_service: VectorService = Depends(get_vector_service),
):
    """API endpoint for getting documents from ChromaDB"""
    viewer = ChromaDBWebViewer(vector_service)

    if category:
        documents = viewer.get_documents_by_category(category)
    else:
        documents = viewer.get_all_documents(limit, offset)

    return documents
