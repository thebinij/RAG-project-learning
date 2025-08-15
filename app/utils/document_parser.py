"""
Document Parser - Converts various file types to text for RAG processing
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from unstructured.partition.auto import partition
from unstructured.documents.elements import Text, Title, NarrativeText, ListItem, Table

logger = logging.getLogger(__name__)


class MultiFormatDocumentParser:
    """
    Parser that converts various file types to text using unstructured library
    Optimized for RAG systems with robust error handling
    """
    
    def __init__(self):
        # Supported file extensions
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
        
        Args:
            file_path: Path to the document to parse
            
        Returns:
            Dict with keys: content, file_type, original_path, conversion_quality, success
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_extension = file_path.suffix.lower()
        
        if file_extension not in self.supported_extensions:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        try:
            # Parse document using unstructured library
            elements = self._parse_with_unstructured(file_path)
            
            # Convert elements to text
            content = self._elements_to_text(elements)
            
            # Assess conversion quality
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
    
    def _parse_with_unstructured(self, file_path: Path) -> List:
        """Parse document using unstructured library with fallback strategies"""
        try:
            # Primary parsing attempt
            elements = partition(str(file_path))
            return elements
            
        except Exception as primary_error:
            logger.warning(f"Primary parsing failed for {file_path.name}: {primary_error}")
            
            try:
                # Fallback: try with fast strategy
                elements = partition(str(file_path), strategy="fast")
                return elements
                
            except Exception as fallback_error:
                logger.warning(f"Fast parsing also failed for {file_path.name}: {fallback_error}")
                
                # Final fallback: basic text extraction
                return self._basic_text_extraction(file_path)
    
    def _basic_text_extraction(self, file_path: Path) -> List:
        """Basic text extraction when unstructured parsing fails"""
        try:
            # Try to read as text file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return [Text(content)]
        except Exception:
            # Return error message element
            return [Text(f"# Parsing Error\n\nCould not parse {file_path.name}")]
    
    def _elements_to_text(self, elements: List) -> str:
        """Convert unstructured elements to clean text"""
        if not elements:
            return ""
        
        text_lines = []
        
        for element in elements:
            if not hasattr(element, 'text') or not element.text:
                continue
                
            text = element.text.strip()
            if not text:
                continue
            
            # Handle different element types
            if isinstance(element, Title):
                # Add title with markdown formatting
                text_lines.append(f"# {text}")
            elif isinstance(element, NarrativeText):
                # Add narrative text
                text_lines.append(text)
            elif isinstance(element, ListItem):
                # Add list item
                text_lines.append(f"- {text}")
            elif isinstance(element, Table):
                # Handle table content
                table_text = self._extract_table_text(element)
                if table_text:
                    text_lines.append(table_text)
            else:
                # Generic text element
                text_lines.append(text)
            
            # Add spacing between elements
            text_lines.append("")
        
        return "\n".join(text_lines).strip()
    
    def _extract_table_text(self, table_element) -> Optional[str]:
        """Extract readable text from table element"""
        if not hasattr(table_element, 'text') or not table_element.text:
            return None
        
        table_text = table_element.text.strip()
        if not table_text:
            return None
        
        # Try to format as markdown table
        lines = table_text.split('\n')
        if len(lines) < 2:
            return table_text
        
        # Simple table formatting
        formatted_lines = []
        
        # Header
        header = lines[0]
        if '\t' in header:
            headers = header.split('\t')
        else:
            headers = re.split(r'\s{2,}', header)
        
        if len(headers) > 1:
            formatted_lines.append("| " + " | ".join(headers) + " |")
            formatted_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
            
            # Data rows
            for line in lines[1:]:
                if '\t' in line:
                    cells = line.split('\t')
                else:
                    cells = re.split(r'\s{2,}', line)
                
                # Ensure consistent row length
                while len(cells) < len(headers):
                    cells.append("")
                cells = cells[:len(headers)]
                
                # Escape pipe characters
                escaped_cells = [cell.replace("|", "\\|").strip() for cell in cells]
                formatted_lines.append("| " + " | ".join(escaped_cells) + " |")
            
            return "\n".join(formatted_lines)
        
        return table_text
    
    def _assess_conversion_quality(self, content: str, file_type: str, elements: List) -> str:
        """Assess the quality of the document conversion"""
        if not content or len(content.strip()) < 10:
            return "poor"
        
        # Check element count
        if elements and len(elements) == 0:
            return "poor"
        
        # Quality assessment based on file type
        if file_type in self.document_formats:
            return self._assess_document_quality(content)
        elif file_type in self.text_formats:
            return self._assess_text_quality(content)
        elif file_type in self.spreadsheet_formats:
            return self._assess_spreadsheet_quality(content)
        elif file_type in self.presentation_formats:
            return self._assess_presentation_quality(content)
        elif file_type in self.image_formats:
            return self._assess_image_quality(content)
        else:
            return self._assess_generic_quality(content)
    
    def _assess_document_quality(self, content: str) -> str:
        """Assess quality of document format conversions"""
        if "# " in content and "## " in content:
            return "excellent"
        elif "# " in content:
            return "good"
        elif len(content) > 200:
            return "fair"
        else:
            return "poor"
    
    def _assess_text_quality(self, content: str) -> str:
        """Assess quality of text format conversions"""
        if len(content) > 100:
            return "excellent"
        elif len(content) > 50:
            return "good"
        else:
            return "fair"
    
    def _assess_spreadsheet_quality(self, content: str) -> str:
        """Assess quality of spreadsheet conversions"""
        if "|" in content and "---" in content:
            return "excellent"
        elif "|" in content:
            return "good"
        elif len(content) > 100:
            return "fair"
        else:
            return "poor"
    
    def _assess_presentation_quality(self, content: str) -> str:
        """Assess quality of presentation conversions"""
        if "# " in content and content.count("# ") > 2:
            return "excellent"
        elif "# " in content:
            return "good"
        elif len(content) > 100:
            return "fair"
        else:
            return "poor"
    
    def _assess_image_quality(self, content: str) -> str:
        """Assess quality of OCR conversions"""
        if len(content) > 200:
            return "excellent"
        elif len(content) > 100:
            return "good"
        elif len(content) > 50:
            return "fair"
        else:
            return "poor"
    
    def _assess_generic_quality(self, content: str) -> str:
        """Generic quality assessment"""
        if len(content) > 200:
            return "good"
        elif len(content) > 100:
            return "fair"
        else:
            return "poor"
