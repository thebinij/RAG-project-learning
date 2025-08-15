"""
Document Parser Utilities - Converts various file types to Markdown for RAG processing

This module provides utilities for parsing different document formats and converting
them to Markdown for consistent processing in the RAG system using the unstructured library.
"""

import re
from pathlib import Path
from typing import Dict, List, Any
import logging

from unstructured.partition.auto import partition
from unstructured.documents.elements import Text, Title, NarrativeText, ListItem, Table

logger = logging.getLogger(__name__)


class MultiFormatDocumentParser:
    """Parser that converts various file types to Markdown using unstructured library"""
    
    def __init__(self):
        
        # Supported extensions that unstructured can handle
        self.supported_extensions = {
            # Document formats
            '.pdf', '.docx', '.doc', '.rtf', '.odt', '.pages',
            # Text formats
            '.txt', '.md', '.markdown',
            # Web formats
            '.html', '.htm', '.xml',
            # Email formats
            '.eml', '.msg',
            # Spreadsheet formats
            '.csv', '.xlsx', '.xls', '.ods',
            # Presentation formats
            '.pptx', '.ppt', '.odp',
            # Image formats (OCR)
            '.png', '.jpg', '.jpeg', '.tiff', '.bmp',
            # Archive formats
            '.zip', '.tar', '.gz'
        }
        
        # File type groups for quality assessment
        self.text_formats = {'.txt', '.md', '.markdown', '.html', '.htm', '.xml'}
        self.document_formats = {'.pdf', '.docx', '.doc', '.rtf', '.odt', '.pages'}
        self.spreadsheet_formats = {'.csv', '.xlsx', '.xls', '.ods'}
        self.presentation_formats = {'.pptx', '.ppt', '.odp'}
        self.image_formats = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if file type is supported"""
        return file_path.suffix.lower() in self.supported_extensions
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file extensions"""
        return list(self.supported_extensions)
    
    def parse_document(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse any supported document type using unstructured library
        
        Returns:
            Dict with keys: content, file_type, original_path, conversion_quality
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_extension = file_path.suffix.lower()
        
        if file_extension not in self.supported_extensions:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        try:
            # Use unstructured library to parse the document
            elements = partition(str(file_path))
            
            # Convert elements to markdown
            content = self._elements_to_markdown(elements)
            
            # Determine conversion quality
            quality = self._assess_conversion_quality(content, file_extension, elements)
            
            return {
                "content": content,
                "file_type": file_extension,
                "original_path": str(file_path),
                "conversion_quality": quality,
                "success": True,
                "element_count": len(elements)
            }
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return {
                "content": f"# Parsing Error\n\nCould not parse {file_path.name}: {str(e)}",
                "file_type": file_extension,
                "original_path": str(file_path),
                "conversion_quality": "error",
                "success": False,
                "error": str(e)
            }
    
    def _elements_to_markdown(self, elements) -> str:
        """Convert unstructured elements to markdown format"""
        markdown_lines = []
        
        for element in elements:
            if isinstance(element, Title):
                # Handle titles
                text = element.text.strip()
                if text:
                    markdown_lines.append(f"# {text}")
            elif isinstance(element, NarrativeText):
                # Handle narrative text (paragraphs)
                text = element.text.strip()
                if text:
                    markdown_lines.append(text)
                    markdown_lines.append("")  # Add spacing
            elif isinstance(element, ListItem):
                # Handle list items
                text = element.text.strip()
                if text:
                    markdown_lines.append(f"- {text}")
            elif isinstance(element, Table):
                # Handle tables
                if hasattr(element, 'text') and element.text:
                    # Try to parse table structure
                    table_md = self._parse_table_text(element.text)
                    if table_md:
                        markdown_lines.append(table_md)
                        markdown_lines.append("")
            elif isinstance(element, Text):
                # Handle generic text elements
                text = element.text.strip()
                if text:
                    # Check if it looks like a header
                    if self._looks_like_header(text):
                        markdown_lines.append(f"## {text}")
                    else:
                        markdown_lines.append(text)
                        markdown_lines.append("")
        
        return "\n".join(markdown_lines).strip()
    
    def _parse_table_text(self, table_text: str) -> str:
        """Parse table text and convert to markdown table format"""
        lines = table_text.strip().split('\n')
        if len(lines) < 2:
            return table_text
        
        # Try to detect table structure
        markdown_lines = []
        
        # First line as header
        header_line = lines[0]
        if '\t' in header_line:
            headers = header_line.split('\t')
        else:
            # Try to split by multiple spaces
            headers = re.split(r'\s{2,}', header_line)
        
        if len(headers) > 1:
            markdown_lines.append("| " + " | ".join(headers) + " |")
            markdown_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
            
            # Data rows
            for line in lines[1:]:
                if '\t' in line:
                    cells = line.split('\t')
                else:
                    cells = re.split(r'\s{2,}', line)
                
                # Ensure row has same length as headers
                while len(cells) < len(headers):
                    cells.append("")
                cells = cells[:len(headers)]  # Truncate if longer
                
                # Escape pipe characters
                escaped_cells = [cell.replace("|", "\\|").strip() for cell in cells]
                markdown_lines.append("| " + " | ".join(escaped_cells) + " |")
            
            return "\n".join(markdown_lines)
        
        return table_text
    
    def _looks_like_header(self, text: str) -> bool:
        """Check if text looks like a header"""
        # All caps and reasonable length
        if text.isupper() and 3 < len(text) < 100:
            return True
        
        # Ends with common header patterns
        if re.search(r'[:：]$', text):
            return True
        
        # Contains common header words
        header_words = ['introduction', 'conclusion', 'summary', 'overview', 'background']
        if any(word in text.lower() for word in header_words):
            return True
        
        return False
    
    def _assess_conversion_quality(self, content: str, file_type: str, elements=None) -> str:
        """Assess the quality of the conversion"""
        if not content or len(content.strip()) < 10:
            return "poor"
        
        # Check element count if available
        if elements and len(elements) == 0:
            return "poor"
        
        # Check for common conversion artifacts and content structure
        if file_type in self.document_formats:
            # Check for structured content
            if "# " in content and "## " in content:
                return "excellent"
            elif "# " in content or "## " in content:
                return "good"
            elif len(content) > 200:
                return "fair"
            else:
                return "poor"
        
        elif file_type in self.text_formats:
            # Text formats should convert well
            if len(content) > 100:
                return "excellent"
            elif len(content) > 50:
                return "good"
            else:
                return "fair"
        
        elif file_type in self.spreadsheet_formats:
            # Check for table structure
            if "|" in content and "---" in content:
                return "excellent"
            elif "|" in content:
                return "good"
            elif len(content) > 100:
                return "fair"
            else:
                return "poor"
        
        elif file_type in self.presentation_formats:
            # Check for slide structure
            if "# " in content and content.count("# ") > 2:
                return "excellent"
            elif "# " in content:
                return "good"
            elif len(content) > 100:
                return "fair"
            else:
                return "poor"
        
        elif file_type in self.image_formats:
            # OCR quality assessment
            if len(content) > 200:
                return "excellent"
            elif len(content) > 100:
                return "good"
            elif len(content) > 50:
                return "fair"
            else:
                return "poor"
        
        # Default assessment
        if len(content) > 200:
            return "good"
        elif len(content) > 100:
            return "fair"
        else:
            return "poor"
