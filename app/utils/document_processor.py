"""
Document Processor - Handles chunking and processing of documents for RAG systems
"""

import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .document_parser import MultiFormatDocumentParser


@dataclass
class ChunkConfig:
    """Configuration for document chunking"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    max_chunk_size: int = 2000


@dataclass
class DocumentMetadata:
    """Standardized document metadata"""
    title: str
    category: str
    filename: str
    chunk_index: int
    total_chunks: int
    file_type: str
    conversion_quality: str
    chunk_size: int


class DocumentProcessor:
    """
    Document processor optimized for RAG systems with robust chunking strategies
    """
    
    def __init__(self, vector_engine, chunk_config: Optional[ChunkConfig] = None):
        self.vector_engine = vector_engine
        self.docs_path = Path("data/knowledge-docs")
        self.parser = MultiFormatDocumentParser()
        self.chunk_config = chunk_config or ChunkConfig()
        
        # Validate chunk configuration
        self._validate_chunk_config()
    
    def _validate_chunk_config(self):
        """Validate chunk configuration parameters"""
        if self.chunk_config.chunk_size < 100:
            raise ValueError("Chunk size must be at least 100 characters")
        if self.chunk_config.chunk_overlap >= self.chunk_config.chunk_size:
            raise ValueError("Chunk overlap must be less than chunk size")
        if self.chunk_config.min_chunk_size > self.chunk_config.chunk_size:
            raise ValueError("Minimum chunk size cannot exceed chunk size")
    
    def process_all_documents(self) -> Dict[str, Any]:
        """Process all documents in the knowledge docs folder"""
        print("🔄 Starting document processing...")
        
        # Clear existing data
        self.vector_engine.clear_collection()
        
        processed_count = 0
        total_chunks = 0
        conversion_stats = {"excellent": 0, "good": 0, "fair": 0, "poor": 0, "error": 0}
        
        # Process each category
        for category_dir in self.docs_path.iterdir():
            if not category_dir.is_dir():
                continue
                
            category_name = category_dir.name
            print(f"\n📁 Processing category: {category_name}")
            
            category_docs, category_chunks = self._process_category(category_dir, category_name)
            processed_count += category_docs
            total_chunks += category_chunks
            
            # Update conversion stats
            if category_docs > 0:
                conversion_stats["excellent"] += category_docs
        
        print(f"\n✅ Processing complete!")
        print(f"📊 Total documents processed: {processed_count}")
        print(f"📝 Total chunks created: {total_chunks}")
        
        return {
            "processed": processed_count,
            "chunks": total_chunks,
            "conversion_stats": conversion_stats
        }
    
    def _process_category(self, category_dir: Path, category_name: str) -> tuple[int, int]:
        """Process all documents in a specific category"""
        category_chunks = 0
        category_docs = 0
        
        # Get all supported files in category
        supported_files = self._get_supported_files(category_dir)
        
        if not supported_files:
            print(f"  ⚠️  No supported files found in {category_name}")
            return 0, 0
        
        for file_path in supported_files:
            try:
                chunks = self._process_single_document(file_path, category_name)
                category_chunks += len(chunks)
                category_docs += 1
                print(f"  ✓ {file_path.name} ({len(chunks)} chunks)")
                
            except Exception as e:
                print(f"  ✗ {file_path.name} - Error: {e}")
        
        return category_docs, category_chunks
    
    def _get_supported_files(self, category_dir: Path) -> List[Path]:
        """Get all supported files in a category directory"""
        supported_files = []
        for ext in self.parser.get_supported_formats():
            supported_files.extend(category_dir.glob(f"*{ext}"))
        return sorted(supported_files)
    
    def _process_single_document(self, file_path: Path, category: str) -> List[Dict[str, Any]]:
        """Process a single document into chunks"""
        if not self.parser.can_parse(file_path):
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
        
        # Parse document
        parsed_result = self.parser.parse_document(file_path)
        
        if not parsed_result["success"]:
            print(f"  ⚠️  Warning: {file_path.name} had parsing issues")
        
        # Clean content
        cleaned_content = self._clean_text_content(parsed_result["content"])
        
        if not cleaned_content or len(cleaned_content.strip()) < 50:
            print(f"  ⚠️  Warning: {file_path.name} has insufficient content after cleaning")
            return []
        
        # Create chunks
        chunks = self._create_chunks(cleaned_content)
        
        if not chunks:
            print(f"  ⚠️  Warning: {file_path.name} produced no valid chunks")
            return []
        
        # Process chunks and add to vector store
        processed_chunks = []
        doc_id = hashlib.md5(str(file_path).encode()).hexdigest()
        
        for i, chunk_text in enumerate(chunks):
            chunk_data = self._create_chunk_data(
                doc_id, i, chunk_text, file_path, category, parsed_result, len(chunks)
            )
            
            # Add to vector store
            self.vector_engine.add_document(
                chunk_data["id"], chunk_text, chunk_data["metadata"]
            )
            
            processed_chunks.append(chunk_data)
        
        return processed_chunks
    
    def _create_chunk_data(self, doc_id: str, chunk_index: int, chunk_text: str, 
                          file_path: Path, category: str, parsed_result: Dict, 
                          total_chunks: int) -> Dict[str, Any]:
        """Create standardized chunk data structure"""
        title = self._extract_title(chunk_text, file_path, category)
        
        metadata = DocumentMetadata(
            title=title,
            category=category,
            filename=file_path.name,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            file_type=parsed_result["file_type"],
            conversion_quality=parsed_result["conversion_quality"],
            chunk_size=len(chunk_text)
        )
        
        # Add backward compatibility fields
        metadata_dict = metadata.__dict__.copy()
        metadata_dict["file"] = file_path.name  # Add 'file' field for compatibility
        
        return {
            "id": f"{doc_id}_{chunk_index}",
            "text": chunk_text,
            "metadata": metadata_dict
        }
    
    def _extract_title(self, chunk_text: str, file_path: Path, category: str) -> str:
        """Extract meaningful title from chunk or file"""
        # Try to extract from markdown header
        header_match = re.search(r"^#\s+(.+)$", chunk_text, re.MULTILINE)
        if header_match:
            title = header_match.group(1).strip()
            if len(title) > 3:
                return title
        
        # Try first meaningful line
        lines = chunk_text.split('\n')
        for line in lines[:3]:
            line = line.strip()
            if line and len(line) > 10 and len(line) < 100:
                if not line.isupper() and not line.islower():
                    clean_line = re.sub(r'[^\w\s\-\.]', '', line)
                    if len(clean_line) > 5:
                        return clean_line
        
        # Use filename
        filename = file_path.stem
        if filename and len(filename) > 2:
            clean_name = filename.replace('_', ' ').replace('-', ' ')
            clean_name = re.sub(r'[^\w\s]', '', clean_name)
            if len(clean_name) > 3:
                return clean_name.title()
        
        # Category fallback
        return f"{category.title()} Document"
    
    def _create_chunks(self, text: str) -> List[str]:
        """
        Create high-quality chunks using sentence-aware chunking strategy
        """
        if not text or not text.strip():
            return []
        
        # For very short texts, return as single chunk
        if len(text.strip()) < self.chunk_config.min_chunk_size:
            return [text.strip()]
        
        # Clean and normalize text
        text = self._clean_text_content(text)
        text = re.sub(r'\n{3,}', '\n\n', text).strip()
        
        # Use sentence-based chunking for better quality
        chunks = self._sentence_based_chunking(text)
        
        # Validate chunks and fallback if needed
        if not self._validate_chunks(chunks):
            print("  ⚠️  Sentence chunking failed, using fallback strategy")
            chunks = self._fallback_chunking(text)
        
        return chunks
    
    def _sentence_based_chunking(self, text: str) -> List[str]:
        """Create chunks based on sentence boundaries"""
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) + 1 <= self.chunk_config.chunk_size:
                current_chunk += (" " + sentence) if current_chunk else sentence
            else:
                # Finalize current chunk
                if current_chunk and len(current_chunk) >= self.chunk_config.min_chunk_size:
                    chunks.append(current_chunk.strip())
                
                # Start new chunk
                current_chunk = sentence
        
        # Add final chunk
        if current_chunk and len(current_chunk) >= self.chunk_config.min_chunk_size:
            chunks.append(current_chunk.strip())
        
        # If no chunks were created (text too small), create a single chunk
        if not chunks and text.strip():
            chunks.append(text.strip())
        
        return chunks
    
    def _fallback_chunking(self, text: str) -> List[str]:
        """Simple character-based chunking as fallback"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_config.chunk_size
            
            if end < len(text):
                # Try to find a good break point
                break_point = self._find_break_point(text, start, end)
                if break_point > start + self.chunk_config.chunk_size // 2:
                    end = break_point
            
            chunk = text[start:end].strip()
            if chunk and len(chunk) >= self.chunk_config.min_chunk_size:
                chunks.append(chunk)
            
            # Move to next chunk with overlap
            start = max(start + 1, end - self.chunk_config.chunk_overlap)
            
            if start >= len(text):
                break
        
        return chunks
    
    def _find_break_point(self, text: str, start: int, end: int) -> int:
        """Find the best break point within a range"""
        # Priority: sentence end, then word boundary, then space
        for i in range(end - 1, start, -1):
            if text[i] in '.!?':
                return i + 1
        
        for i in range(end - 1, start, -1):
            if text[i].isspace():
                return i + 1
        
        return end
    
    def _validate_chunks(self, chunks: List[str]) -> bool:
        """Validate that chunks meet quality standards"""
        if not chunks:
            return False
        
        # Check minimum chunk size
        if any(len(chunk) < self.chunk_config.min_chunk_size for chunk in chunks):
            return False
        
        # Check for reasonable chunk distribution
        avg_size = sum(len(chunk) for chunk in chunks) / len(chunks)
        if avg_size < self.chunk_config.min_chunk_size * 1.5:
            return False
        
        return True
    
    def _clean_text_content(self, text: str) -> str:
        """Clean text content for better chunking"""
        if not text:
            return text
        
        # Remove common PDF artifacts
        cleaned = text
        
        # Remove LaTeX and math symbols
        cleaned = re.sub(r'\\[a-zA-Z]+(\{[^}]*\})?', '', cleaned)
        cleaned = re.sub(r'\$[^$]*\$', '', cleaned)
        
        # Remove non-ASCII characters
        cleaned = re.sub(r'[^\x00-\x7F]+', '', cleaned)
        
        # Keep only readable characters
        cleaned = re.sub(r'[^\w\s\.,!?;:()\[\]{}"\'-]', '', cleaned)
        
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Filter lines with sufficient English content
        lines = cleaned.split('\n')
        filtered_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check English content ratio
            english_chars = len(re.findall(r'[a-zA-Z]', line))
            total_chars = len(line)
            
            if total_chars > 0 and english_chars / total_chars > 0.3:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def process_document(self, file_path: Path, category: str) -> List[Dict[str, Any]]:
        """Legacy method for backward compatibility"""
        return self._process_single_document(file_path, category)
    
    def chunk_text_by_strategy(self, text: str, strategy: str = "sentence") -> List[str]:
        """Chunk text using specified strategy"""
        if strategy == "sentence":
            return self._sentence_based_chunking(text)
        elif strategy == "fallback":
            return self._fallback_chunking(text)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
