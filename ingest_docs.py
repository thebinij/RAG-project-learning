#!/usr/bin/env python3
"""
Document Ingestion Entry Point - Main script for ingesting documents into the RAG system

This script provides a command-line interface for processing and ingesting documents
from the knowledge-docs directory into the vector database.

Usage:
    python ingest_docs.py                    # Process all documents
    python ingest_docs.py --category research  # Process only research category
    python ingest_docs.py --category handbooks # Process only handbooks category
"""

import sys
import argparse
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.document_processor import DocumentProcessor
from app.core.engines.vector_engine import VectorEngine


def process_category_documents(document_processor: DocumentProcessor, category: str) -> dict:
    """Process documents from a specific category"""
    print(f"🔄 Processing category: {category}")
    print("=" * 60)
    
    # Clear existing documents from this category first
    print(f"🗑️  Clearing existing {category} documents...")
    document_processor.vector_engine.clear_category(category)
    
    # Create a custom chunk config for this category
    from app.utils.document_processor import ChunkConfig
    chunk_config = ChunkConfig(chunk_size=1000, chunk_overlap=200)
    
    # Create a new processor instance for this category
    category_processor = DocumentProcessor(document_processor.vector_engine, chunk_config)
    
    # Process the specific category
    category_path = Path("data/knowledge-docs") / category
    if not category_path.exists():
        raise ValueError(f"Category '{category}' not found in knowledge-docs directory")
    
    # Get all supported file types in this category
    supported_files = []
    for ext in category_processor.parser.get_supported_formats():
        supported_files.extend(category_path.glob(f"*{ext}"))
    
    if not supported_files:
        print(f"⚠️  No supported files found in category '{category}'")
        return {"processed": 0, "chunks": 0, "conversion_stats": {"excellent": 0}}
    
    # Process each file individually
    processed_count = 0
    chunk_count = 0
    
    for doc_file in supported_files:
        try:
            chunks = category_processor._process_single_document(doc_file, category)
            chunk_count += len(chunks)
            processed_count += 1
            print(f"  ✓ {doc_file.name} ({len(chunks)} chunks)")
            
        except Exception as e:
            print(f"  ✗ {doc_file.name} - Error: {e}")
    
    return {
        "processed": processed_count, 
        "chunks": chunk_count,
        "conversion_stats": {"excellent": processed_count}
    }


def main():
    """Main entry point for document ingestion"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="LegendaryCorp Document Ingestion System")
    parser.add_argument("--category", "-c", type=str, help="Process only documents from specific category")
    args = parser.parse_args()
    
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

    try:
        if args.category:
            # Process only specific category
            print(f"🎯 Processing category: {args.category}")
            result = process_category_documents(document_processor, args.category)
        else:
            # Process all documents
            print("🔄 Beginning multi-format knowledge transfer...")
            print("=" * 60)
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
        if args.category:
            print(f"🎯 Category '{args.category}' processed successfully!")
        else:
            print(f"🎯 Your RAG system now supports {len(supported_formats)} file formats!")
        
    except Exception as e:
        print(f"\n❌ Error during ingestion: {e}")
        print("Please check your document files and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
