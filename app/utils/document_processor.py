"""
Document Processor - Handles chunking and processing of LegendaryCorp documents
"""

import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List

from .document_parser import MultiFormatDocumentParser


class DocumentProcessor:
    def __init__(self, vector_engine):
        self.vector_engine = vector_engine
        self.docs_path = Path(__file__).parent.parent.parent.parent / "knowledge-docs"
        
        # Initialize multi-format document parser
        self.parser = MultiFormatDocumentParser()

        # Chunking parameters
        self.chunk_size = 500  # characters
        self.chunk_overlap = 100  # characters

    def process_all_documents(self) -> Dict[str, int]:
        """Process all documents in the LegendaryCorp docs folder"""
        processed_count = 0
        chunk_count = 0
        conversion_stats = {"excellent": 0, "good": 0, "fair": 0, "poor": 0, "error": 0}

        # Clear existing data
        self.vector_engine.clear_collection()

        # Process each category
        for category in self.docs_path.iterdir():
            if category.is_dir():
                print(f"\nProcessing category: {category.name}")
                
                # Get all supported file types
                supported_files = []
                for ext in self.parser.get_supported_formats():
                    supported_files.extend(category.glob(f"*{ext}"))
                
                for doc_file in supported_files:
                    try:
                        chunks = self.process_document(doc_file, category.name)
                        chunk_count += len(chunks)
                        processed_count += 1
                        
                        # Track conversion quality from metadata
                        if chunks and len(chunks) > 0:
                            first_chunk = chunks[0]
                            if isinstance(first_chunk, dict) and 'metadata' in first_chunk:
                                quality = first_chunk['metadata'].get('conversion_quality', 'unknown')
                                conversion_stats[quality] = conversion_stats.get(quality, 0) + 1
                        
                        print(f"  ✓ {doc_file.name} ({len(chunks)} chunks)")
                        
                    except Exception as e:
                        print(f"  ✗ {doc_file.name} - Error: {e}")
                        conversion_stats["error"] += 1

        # Print conversion statistics
        print(f"\n📊 Conversion Quality Summary:")
        for quality, count in conversion_stats.items():
            if count > 0:
                print(f"  {quality.title()}: {count} files")

        return {
            "processed": processed_count, 
            "chunks": chunk_count,
            "conversion_stats": conversion_stats
        }

    def process_document(self, file_path: Path, category: str) -> List[Dict[str, Any]]:
        """Process a single document into chunks"""
        
        # Check if file is supported
        if not self.parser.can_parse(file_path):
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
        
        # Parse document using multi-format parser
        parsed_result = self.parser.parse_document(file_path)
        
        if not parsed_result["success"]:
            print(f"  ⚠️  Warning: {file_path.name} had parsing issues")
        
        # Extract metadata from document
        title = self._extract_title(parsed_result["content"])
        doc_id = hashlib.md5(str(file_path).encode()).hexdigest()
        
        # Add conversion metadata
        conversion_metadata = {
            "original_file_type": parsed_result["file_type"],
            "conversion_quality": parsed_result["conversion_quality"],
            "conversion_success": parsed_result["success"]
        }
        
        if not parsed_result["success"]:
            conversion_metadata["conversion_error"] = parsed_result.get("error", "Unknown error")

        # Create chunks from converted markdown content
        chunks = self._create_chunks(parsed_result["content"])

        # Process each chunk
        processed_chunks = []
        for i, chunk_text in enumerate(chunks):
            chunk_data = {
                "id": f"{doc_id}_{i}",
                "text": chunk_text,
                "metadata": {
                    "title": title or file_path.stem.replace("-", " ").title(),
                    "category": category,
                    "file": file_path.name,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    **conversion_metadata
                },
            }

            # Add to vector store
            self.vector_engine.add_document(
                chunk_data["id"], chunk_text, chunk_data["metadata"]
            )

            processed_chunks.append(chunk_data)

        return processed_chunks

    def _extract_title(self, content: str) -> str:
        """Extract title from markdown document"""
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        return match.group(1) if match else None

    def _create_chunks(self, text: str) -> List[str]:
        """Create overlapping chunks from text"""
        chunks = []

        # Simple chunking by character count with overlap
        start = 0
        while start < len(text):
            end = start + self.chunk_size

            # Try to find a good break point (end of sentence or paragraph)
            if end < len(text):
                # Look for sentence end
                sentence_end = text.rfind(".", start, end)
                if sentence_end > start + self.chunk_size // 2:
                    end = sentence_end + 1
                else:
                    # Look for paragraph break
                    para_break = text.rfind("\n\n", start, end)
                    if para_break > start + self.chunk_size // 2:
                        end = para_break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - self.chunk_overlap

        return chunks

    def chunk_text_by_strategy(self, text: str, strategy: str = "fixed") -> List[str]:
        """Chunk text using different strategies for lab exercises"""
        if strategy == "fixed":
            return self._create_chunks(text)

        elif strategy == "sentence":
            # Split by sentences
            sentences = re.split(r"(?<=[.!?])\s+", text)
            chunks = []
            current_chunk = ""

            for sentence in sentences:
                if len(current_chunk) + len(sentence) <= self.chunk_size:
                    current_chunk += " " + sentence
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence

            if current_chunk:
                chunks.append(current_chunk.strip())

            return chunks

        elif strategy == "paragraph":
            # Split by paragraphs
            paragraphs = text.split("\n\n")
            chunks = []

            for para in paragraphs:
                if len(para) <= self.chunk_size:
                    chunks.append(para.strip())
                else:
                    # Split large paragraphs
                    sub_chunks = self._create_chunks(para)
                    chunks.extend(sub_chunks)

            return chunks

        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
