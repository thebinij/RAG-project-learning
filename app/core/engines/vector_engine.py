"""
Vector Engine - Manages vector database operations using ChromaDB
"""

import os
from datetime import datetime
from typing import Any, Dict, List

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class VectorEngine:
    def __init__(self, collection_name: str = "LegendaryCorp_docs"):
        print("[VectorEngine] Initializing ChromaDB...")

        # Fix HuggingFace tokenizers parallelism warning
        os.environ["TOKENIZERS_PARALLELISM"] = "false"

        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(
            path="./data/vector_db", settings=Settings(anonymized_telemetry=False)
        )

        # Initialize embedding model
        os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "0"  # Allow downloading

        print("[VectorEngine] Loading embedding model...")
        print("[VectorEngine] Note: First-time download may take 2-3 minutes (~90MB)")

        try:
            # Try to load model with progress indication
            import sys

            sys.stdout.flush()
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
            print("[VectorEngine] Model loaded successfully!")
        except Exception as e:
            print(f"[VectorEngine] Error loading model: {e}")
            print("[VectorEngine] Attempting offline mode...")
            # Try to work offline if model exists
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            import warnings

            warnings.filterwarnings("ignore")
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

        self.last_updated = datetime.now()

    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        """Add a document chunk to the vector store"""
        # Generate embedding
        embedding = self.embedding_model.encode(text).tolist()

        # Add to collection
        self.collection.add(
            ids=[doc_id], embeddings=[embedding], documents=[text], metadatas=[metadata]
        )

        self.last_updated = datetime.now()

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents using semantic similarity with enhanced metadata"""
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()

        # Search in collection with more results for better selection
        search_limit = min(limit * 2, 20)  # Get more results initially for better filtering
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=search_limit,
            include=["documents", "metadatas", "distances"],
        )

        # Format and filter results
        formatted_results = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                metadata = results["metadatas"][0][i]
                score = 1 - results["distances"][0][i]  # Convert distance to similarity
                
                # Enhanced metadata extraction - handle both old and new field names
                title = metadata.get("title", "Untitled Document")
                category = metadata.get("category", "Unknown Category")
                # Handle both 'file' and 'filename' fields for backward compatibility
                file_name = metadata.get("file") or metadata.get("filename", "Unknown File")
                
                # Smart snippet generation based on category
                content = results["documents"][0][i]
                if category.lower() == 'research':
                    # For research papers, try to get abstract or introduction
                    snippet = self._extract_research_snippet(content)
                else:
                    # For other documents, standard snippet
                    snippet = content[:150] + "..." if len(content) > 150 else content
                
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "text": content,
                    "metadata": {
                        **metadata,
                        "title": title,
                        "category": category,
                        "file": file_name,
                        "enhanced_title": self._enhance_title(title, category)
                    },
                    "score": score,
                    "title": title,
                    "snippet": snippet,
                    "category": category
                })
        
        # Sort by score and return top results
        formatted_results.sort(key=lambda x: x["score"], reverse=True)
        return formatted_results[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        count = self.collection.count()

        # Count unique documents
        all_metadata = self.collection.get()["metadatas"]
        unique_files = set()
        if all_metadata:
            for meta in all_metadata:
                # Handle both 'file' and 'filename' fields
                file_name = meta.get("file") or meta.get("filename", "")
                if file_name:
                    unique_files.add(file_name)

        return {
            "total_chunks": count,
            "total_documents": len(unique_files),
            "last_updated": self.last_updated.isoformat(),
        }

    def clear_collection(self):
        """Clear all documents from the collection"""
        # Delete and recreate collection
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.create_collection(
            name=self.collection.name, metadata={"hnsw:space": "cosine"}
        )
        self.last_updated = datetime.now()

    def clear_category(self, category: str):
        """Clear documents from a specific category"""
        try:
            # Get all documents in the category
            results = self.collection.get(
                where={"category": category},
                include=["ids"]
            )
            
            if results["ids"]:
                # Delete documents from this category
                self.collection.delete(ids=results["ids"])
                print(f"🗑️  Cleared {len(results['ids'])} documents from category: {category}")
            else:
                print(f"ℹ️  No documents found in category: {category}")
                
        except Exception as e:
            print(f"❌ Error clearing category {category}: {e}")
            # Fallback to full collection clear
            self.clear_collection()

    def is_initialized(self) -> bool:
        """Check if the vector store has been initialized with documents"""
        return self.collection.count() > 0

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a text (useful for visualization)"""
        return self.embedding_model.encode(text).tolist()

    def get_visualization_data(self) -> Dict[str, Any]:
        """Get data for vector space visualization"""
        # This is a simplified version - in practice, you'd use dimensionality reduction
        try:
            # Get a sample of documents
            sample = self.collection.get(limit=50, include=["embeddings", "metadatas"])

            if not sample["embeddings"]:
                return {"error": "No documents in collection"}

            # Simple 2D projection using first two dimensions
            points = []
            for i, embedding in enumerate(sample["embeddings"]):
                points.append(
                    {
                        "x": embedding[0],
                        "y": embedding[1],
                        "category": sample["metadatas"][i].get("category", "unknown"),
                        "title": sample["metadatas"][i].get("title", "Unknown"),
                    }
                )

            return {
                "points": points,
                "categories": list(set(p["category"] for p in points)),
            }
        except Exception as e:
            return {"error": str(e)}

    def _extract_research_snippet(self, content: str) -> str:
        """Extract a meaningful snippet from research paper content"""
        if not content:
            return ""
        
        # Try to find abstract or introduction
        content_lower = content.lower()
        
        # Look for common research paper sections
        abstract_markers = ["abstract", "summary", "overview"]
        intro_markers = ["introduction", "background", "overview"]
        
        # Try to find abstract first
        for marker in abstract_markers:
            if marker in content_lower:
                start_idx = content_lower.find(marker)
                # Get text after the marker
                after_marker = content[start_idx + len(marker):]
                # Find the end (next section or reasonable length)
                end_idx = min(400, len(after_marker))
                if end_idx < len(after_marker):
                    # Try to end at a sentence boundary
                    last_period = after_marker[:end_idx].rfind(".")
                    if last_period > 200:
                        end_idx = last_period + 1
                return after_marker[:end_idx].strip()
        
        # If no abstract, try introduction
        for marker in intro_markers:
            if marker in content_lower:
                start_idx = content_lower.find(marker)
                after_marker = content[start_idx + len(marker):]
                end_idx = min(300, len(after_marker))
                if end_idx < len(after_marker):
                    last_period = after_marker[:end_idx].rfind(".")
                    if last_period > 150:
                        end_idx = last_period + 1
                return after_marker[:end_idx].strip()
        
        # Fallback: return first 200 characters with sentence boundary
        if len(content) > 200:
            last_period = content[:200].rfind(".")
            if last_period > 100:
                return content[:last_period + 1].strip()
            return content[:200].strip()
        
        return content.strip()

    def _enhance_title(self, title: str, category: str) -> str:
        """Enhance document title based on category"""
        if not title or title == "Untitled Document":
            return f"Document from {category.title()}"
        
        # Clean up common title issues
        title = title.replace("-", " ").replace("_", " ")
        
        # Add category context if not obvious
        if category.lower() == 'research' and 'research' not in title.lower():
            title = f"{title} (Research Paper)"
        elif category.lower() == 'technical' and 'technical' not in title.lower():
            title = f"{title} (Technical)"
        elif category.lower() == 'handbooks' and 'handbook' not in title.lower():
            title = f"{title} (Handbook)"
        
        return title.title()
