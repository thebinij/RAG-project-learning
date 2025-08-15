"""
Comprehensive Test Suite for MultiFormatDocumentParser

This single test file covers:
✅ Basic structure validation (no external dependencies)
✅ Full functionality testing (requires unstructured library)
✅ Integration testing with real files
✅ Error handling and edge cases
✅ Quality assessment validation

Usage:
- Basic tests: Always run (structure validation)
- Full tests: Run when unstructured library is available
- Integration tests: Run with real file operations

Requirements:
- Basic tests: None (uses mocked dependencies)
- Full tests: pip install 'unstructured[all-docs]'
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestDocumentParserStructure(unittest.TestCase):
    """Basic structure tests for the document parser"""
    
    def test_import_structure(self):
        """Test that the parser module can be imported and has expected structure"""
        try:
            from app.utils.document_parser import MultiFormatDocumentParser
            self.assertTrue(True, "Import successful")
        except ImportError as e:
            self.fail(f"Import failed: {e}")
    
    def test_class_structure(self):
        """Test that the parser class has expected methods and attributes"""
        from app.utils.document_parser import MultiFormatDocumentParser
        
        parser = MultiFormatDocumentParser()
        
        # Test required methods exist
        required_methods = [
            'can_parse', 'get_supported_formats', 'parse_document',
            '_elements_to_markdown', '_parse_table_text', '_looks_like_header',
            '_assess_conversion_quality'
        ]
        for method in required_methods:
            self.assertTrue(hasattr(parser, method), f"Missing method: {method}")
        
        # Test required attributes exist
        required_attrs = [
            'supported_extensions', 'text_formats', 'document_formats',
            'spreadsheet_formats', 'presentation_formats', 'image_formats'
        ]
        for attr in required_attrs:
            self.assertTrue(hasattr(parser, attr), f"Missing attribute: {attr}")
    
    def test_supported_extensions_structure(self):
        """Test that supported extensions are properly categorized"""
        from app.utils.document_parser import MultiFormatDocumentParser
        
        parser = MultiFormatDocumentParser()
        
        # Test that extensions are sets
        self.assertIsInstance(parser.supported_extensions, set)
        self.assertGreater(len(parser.supported_extensions), 20)
        
        # Test that all categorized formats are in supported extensions
        all_categorized = (
            parser.text_formats | parser.document_formats | 
            parser.spreadsheet_formats | parser.presentation_formats | 
            parser.image_formats
        )
        self.assertTrue(all_categorized.issubset(parser.supported_extensions))
    
    def test_file_extension_validation(self):
        """Test that file extension validation works correctly"""
        from app.utils.document_parser import MultiFormatDocumentParser
        
        parser = MultiFormatDocumentParser()
        
        # Test with valid extensions
        valid_extensions = ['.pdf', '.docx', '.csv', '.txt', '.png']
        for ext in valid_extensions:
            self.assertTrue(parser.can_parse(Path(f"document{ext}")))
        
        # Test with invalid extensions
        invalid_extensions = ['.xyz', '.abc', '']
        for ext in invalid_extensions:
            self.assertFalse(parser.can_parse(Path(f"file{ext}")))
    
    def test_supported_formats_list(self):
        """Test that supported formats list is comprehensive"""
        from app.utils.document_parser import MultiFormatDocumentParser
        
        parser = MultiFormatDocumentParser()
        formats = parser.get_supported_formats()
        
        self.assertIsInstance(formats, list)
        self.assertGreater(len(formats), 20)
        
        # Test that common formats are included
        common_formats = ['.pdf', '.docx', '.txt', '.csv', '.png', '.jpg']
        for fmt in common_formats:
            self.assertIn(fmt, formats, f"Common format {fmt} should be supported")


class TestDocumentParserFunctionality(unittest.TestCase):
    """Full functionality tests using real unstructured library"""
    
    def test_parser_initialization(self):
        """Test parser initialization and configuration"""
        from app.utils.document_parser import MultiFormatDocumentParser
        parser = MultiFormatDocumentParser()
        
        # Check supported extensions
        self.assertIsInstance(parser.supported_extensions, set)
        self.assertGreater(len(parser.supported_extensions), 20)
        
        # Check specific format groups
        self.assertIn('.pdf', parser.document_formats)
        self.assertIn('.docx', parser.document_formats)
        self.assertIn('.txt', parser.text_formats)
        self.assertIn('.csv', parser.spreadsheet_formats)
        self.assertIn('.png', parser.image_formats)
    
    def test_document_parsing_success(self):
        """Test successful document parsing"""
        from app.utils.document_parser import MultiFormatDocumentParser
        parser = MultiFormatDocumentParser()
        
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(b"Sample Document Title\n\nThis is a sample paragraph with some content.\n\n- First list item\n- Second list item\n\nGeneric text content")
            tmp_file.flush()
            
            try:
                result = parser.parse_document(Path(tmp_file.name))
                
                # Check result structure
                required_keys = ['content', 'file_type', 'original_path', 
                               'conversion_quality', 'success', 'element_count']
                for key in required_keys:
                    self.assertIn(key, result, f"Missing key: {key}")
                
                # Check success
                self.assertTrue(result['success'])
                self.assertEqual(result['file_type'], '.txt')
                self.assertGreater(result['element_count'], 0)
                
                # Check content conversion
                self.assertIn('Sample Document Title', result['content'])
                self.assertIn('sample paragraph', result['content'])
                self.assertIn('list item', result['content'])
                
            finally:
                os.unlink(tmp_file.name)
    
    def test_document_parsing_error(self):
        """Test document parsing error handling"""
        from app.utils.document_parser import MultiFormatDocumentParser
        parser = MultiFormatDocumentParser()
        
        # Create a temporary file with invalid content that might cause parsing issues
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            # Create content that might cause issues
            tmp_file.write(b"Invalid content with special characters: \x00\x01\x02")
            tmp_file.flush()
            
            try:
                result = parser.parse_document(Path(tmp_file.name))
                # Even with problematic content, the parser should handle it gracefully
                self.assertIn('content', result)
                self.assertIn('file_type', result)
            finally:
                os.unlink(tmp_file.name)
    
    def test_file_not_found_error(self):
        """Test handling of non-existent files"""
        from app.utils.document_parser import MultiFormatDocumentParser
        parser = MultiFormatDocumentParser()
        
        with self.assertRaises(FileNotFoundError):
            parser.parse_document(Path("nonexistent_file.pdf"))
    
    def test_unsupported_file_type(self):
        """Test handling of unsupported file types"""
        from app.utils.document_parser import MultiFormatDocumentParser
        parser = MultiFormatDocumentParser()
        
        # Create a temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix='.unsupported', delete=False) as tmp_file:
            tmp_file.write(b"Some content")
            tmp_file.flush()
            
            try:
                with self.assertRaises(ValueError):
                    parser.parse_document(Path(tmp_file.name))
            finally:
                os.unlink(tmp_file.name)
    
    def test_elements_to_markdown_conversion(self):
        """Test conversion of unstructured elements to markdown"""
        from app.utils.document_parser import MultiFormatDocumentParser
        from unstructured.documents.elements import Title, NarrativeText, ListItem, Table, Text
        
        parser = MultiFormatDocumentParser()
        
        # Create real unstructured elements
        title = Title("Sample Document Title")
        narrative = NarrativeText("This is a sample paragraph with some content.")
        list_item = ListItem("First list item")
        table = Table("Header1\tHeader2\nValue1\tValue2")
        text = Text("Generic text content")
        
        elements = [title, narrative, list_item, table, text]
        
        markdown = parser._elements_to_markdown(elements)
        
        # Check markdown structure
        self.assertIn('Sample Document Title', markdown)
        self.assertIn('sample paragraph', markdown)
        self.assertIn('list item', markdown)
        self.assertIn('Generic text content', markdown)
    
    def test_table_parsing(self):
        """Test table text parsing and conversion"""
        from app.utils.document_parser import MultiFormatDocumentParser
        parser = MultiFormatDocumentParser()
        
        # Test tab-separated table
        table_text = "Name\tAge\tCity\nJohn\t25\tNYC\nJane\t30\tLA"
        table_md = parser._parse_table_text(table_text)
        
        self.assertIn('| Name | Age | City |', table_md)
        self.assertIn('| --- | --- | --- |', table_md)
        self.assertIn('| John | 25 | NYC |', table_md)
        self.assertIn('| Jane | 30 | LA |', table_md)
        
        # Test space-separated table
        table_text = "Name  Age  City\nJohn  25   NYC\nJane  30   LA"
        table_md = parser._parse_table_text(table_text)
        self.assertIn('| Name | Age | City |', table_md)
    
    def test_header_detection(self):
        """Test automatic header detection"""
        from app.utils.document_parser import MultiFormatDocumentParser
        parser = MultiFormatDocumentParser()
        
        # Test all caps header
        self.assertTrue(parser._looks_like_header("INTRODUCTION"))
        self.assertTrue(parser._looks_like_header("CONCLUSION"))
        
        # Test colon-ended header
        self.assertTrue(parser._looks_like_header("Background:"))
        self.assertTrue(parser._looks_like_header("Summary："))
        
        # Test header words
        self.assertTrue(parser._looks_like_header("Project Overview"))
        self.assertTrue(parser._looks_like_header("Technical Background"))
        
        # Test non-headers
        self.assertFalse(parser._looks_like_header("This is a regular sentence"))
        self.assertFalse(parser._looks_like_header(""))
    
    def test_conversion_quality_assessment(self):
        """Test conversion quality assessment logic"""
        from app.utils.document_parser import MultiFormatDocumentParser
        parser = MultiFormatDocumentParser()
        
        # Test document format quality - needs structured content AND sufficient length
        content = "# Title\n## Section\n\nThis is a comprehensive document with multiple sections and detailed content that provides substantial information for the reader to understand the topic thoroughly."
        quality = parser._assess_conversion_quality(content, '.pdf')
        self.assertEqual(quality, 'excellent')
        
        # Test text format quality
        content = "Simple text content with sufficient length that exceeds the minimum threshold for excellent quality assessment in text format processing."
        quality = parser._assess_conversion_quality(content, '.txt')
        self.assertEqual(quality, 'excellent')
        
        # Test spreadsheet format quality
        content = "| Header | Data |\n| --- | --- |\n| Value | Info |"
        quality = parser._assess_conversion_quality(content, '.csv')
        self.assertEqual(quality, 'excellent')
        
        # Test poor quality
        content = "Short"
        quality = parser._assess_conversion_quality(content, '.pdf')
        self.assertEqual(quality, 'poor')


class TestDocumentParserIntegration(unittest.TestCase):
    """Integration tests for document parser with real file operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = Path(tempfile.mkdtemp())
        from app.utils.document_parser import MultiFormatDocumentParser
        self.parser = MultiFormatDocumentParser()
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_markdown_file_processing(self):
        """Test processing of actual markdown files"""
        # Create a test markdown file
        md_content = """# Test Document
        
## Introduction
This is a test document.

## Content
- Point 1
- Point 2

## Conclusion
End of test.
"""
        
        md_file = self.test_dir / "test.md"
        md_file.write_text(md_content)
        
        # Process the file
        result = self.parser.parse_document(md_file)
        
        # Verify results
        self.assertTrue(result['success'])
        self.assertEqual(result['file_type'], '.md')
        self.assertIn('Test Document', result['content'])
        self.assertIn('Introduction', result['content'])
        self.assertIn('Point 1', result['content'])
    
    def test_text_file_processing(self):
        """Test processing of actual text files"""
        # Create a test text file
        txt_content = """LEGENDARYCORP POLICY DOCUMENT
        
This document outlines the company policies.
        
EMPLOYEE BENEFITS
- Health insurance
- 401k matching
- Unlimited PTO
"""
        
        txt_file = self.test_dir / "policy.txt"
        txt_file.write_text(txt_content)
        
        # Process the file
        result = self.parser.parse_document(txt_file)
        
        # Verify results
        self.assertTrue(result['success'])
        self.assertEqual(result['file_type'], '.txt')
        self.assertIn('LEGENDARYCORP POLICY DOCUMENT', result['content'])
        self.assertIn('EMPLOYEE BENEFITS', result['content'])


if __name__ == '__main__':
    # Run comprehensive test suite
    print("🧪 COMPREHENSIVE TESTING OF MULTI-FORMAT DOCUMENT PARSER")
    print("=" * 60)
    print("📋 Test Categories:")
    print("   • Structure Tests: Basic validation")
    print("   • Functionality Tests: Full features with unstructured library")
    print("   • Integration Tests: Real file operations")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestDocumentParserStructure)
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDocumentParserFunctionality))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDocumentParserIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("🎉 ALL TESTS PASSED!")
        print(f"✅ Tests run: {result.testsRun}")
        print("\n💡 Next Steps:")
        print("   • Test with real documents in your data/knowledge-docs directory")
        print("   • Run 'python ingest_docs.py' to process documents")
        print("   • The parser supports multiple file formats including PDF, DOCX, CSV, etc.")
    else:
        print("❌ SOME TESTS FAILED!")
        print(f"✅ Tests run: {result.testsRun}")
        print(f"❌ Failures: {len(result.failures)}")
        print(f"❌ Errors: {len(result.errors)}")
        
        if result.failures or result.errors:
            print("\n💡 Troubleshooting:")
            print("   • Check that 'unstructured[all-docs]' is properly installed")
            print("   • Ensure all dependencies are available")
            print("   • Check the test output for specific error details")
    
    print("=" * 60)
