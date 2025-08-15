#!/usr/bin/env python3
"""
Document Ingestion Entry Point - Main script for ingesting documents into the RAG system

This script provides a command-line interface for processing and ingesting documents
from the knowledge-docs directory into the vector database.

Usage:
    python ingest_docs.py
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.document_processor import DocumentProcessor
from app.core.engines.vector_engine import VectorEngine


def main():
    """Main entry point for document ingestion"""
    print("🚀 LegendaryCorp MULTI-FORMAT KNOWLEDGE INGESTION SYSTEM")
    print("=" * 60)

    # Initialize systems
    print("🔌 Connecting to AI Brain (ChromaDB)...")
    vector_engine = VectorEngine()
    print("✅ Vector engine initialized")

    print("📚 Loading Multi-Format Document Processor...")
    document_processor = DocumentProcessor(vector_engine)
    print("✅ Document processor ready")

    # Show supported formats
    supported_formats = document_processor.parser.get_supported_formats()
    print(f"📋 Supported file formats: {', '.join(supported_formats)}")
    print("All systems online!\n")

    # Process documents
    print("🔄 Beginning multi-format knowledge transfer...")
    print("=" * 60)

    try:
        # Process all documents using the enhanced processor
        result = document_processor.process_all_documents()
        
        print("\n" + "=" * 60)
        print("🎉 INGESTION COMPLETE!")
        print("=" * 60)
        print(f"📊 Statistics:")
        print(f"   • Documents processed: {result['processed']}")
        print(f"   • Knowledge chunks: {result['chunks']}")
        print(f"   • AI IQ increased: +{result['processed']*10} points")
        
        # Show conversion quality breakdown
        if 'conversion_stats' in result:
            print(f"\n🔄 Conversion Quality Breakdown:")
            for quality, count in result['conversion_stats'].items():
                if count > 0:
                    quality_emoji = {
                        'excellent': '🟢',
                        'good': '🟡', 
                        'fair': '🟠',
                        'poor': '🔴',
                        'error': '❌'
                    }.get(quality, '⚪')
                    print(f"   {quality_emoji} {quality.title()}: {count} files")
        
        print(f"\n💰 Value delivered: ${result['processed']*50}K in searchable knowledge!")
        print(f"🎯 Your RAG system now supports {len(supported_formats)} file formats!")
        
    except Exception as e:
        print(f"\n❌ Error during ingestion: {e}")
        print("Please check your document files and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
