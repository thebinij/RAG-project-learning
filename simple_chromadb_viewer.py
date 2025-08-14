#!/usr/bin/env python3
"""
Simple ChromaDB Viewer - No external dependencies required
"""

import chromadb
import json
from pathlib import Path

class SimpleChromaDBViewer:
    def __init__(self, db_path="./chroma_db"):
        """Initialize the viewer with ChromaDB connection"""
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_collection("LegendaryCorp_docs")
        
    def show_basic_stats(self):
        """Show basic database statistics"""
        print("🔍 ChromaDB Basic Statistics")
        print("=" * 40)
        
        total_chunks = self.collection.count()
        print(f"Total chunks: {total_chunks}")
        
        if total_chunks == 0:
            print("No documents found in database!")
            return
        
        # Get a sample to show structure
        sample = self.collection.get(limit=1, include=["metadatas", "documents"])
        if sample['metadatas']:
            print(f"Sample metadata keys: {list(sample['metadatas'][0].keys())}")
            print(f"Sample document length: {len(sample['documents'][0])} characters")
    
    def list_all_documents(self, limit=None):
        """List all documents with their metadata"""
        print("\n📚 All Documents in Database")
        print("=" * 40)
        
        # Get all documents
        all_docs = self.collection.get(include=["metadatas", "documents"])
        
        if not all_docs['metadatas']:
            print("No documents found!")
            return
        
        total = len(all_docs['metadatas'])
        if limit:
            total = min(total, limit)
        
        print(f"Showing {total} documents:")
        
        for i in range(total):
            meta = all_docs['metadatas'][i]
            doc = all_docs['documents'][i]
            
            print(f"\n--- Document {i+1} ---")
            print(f"File: {meta.get('file', 'Unknown')}")
            print(f"Category: {meta.get('category', 'Unknown')}")
            print(f"Title: {meta.get('title', 'No title')}")
            print(f"Chunk: {meta.get('chunk_index', 'N/A')} of {meta.get('total_chunks', 'N/A')}")
            print(f"Content: {doc[:100]}...")
            
            if limit and i >= limit - 1:
                break
    
    def search_documents(self, query, limit=5):
        """Search for documents using semantic search"""
        print(f"\n🔍 Searching for: '{query}'")
        print("=" * 40)
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                include=["documents", "metadatas", "distances"]
            )
            
            if results['metadatas'] and len(results['metadatas'][0]) > 0:
                print(f"Found {len(results['metadatas'][0])} relevant chunks:")
                
                for i, (doc, meta, distance) in enumerate(zip(
                    results['documents'][0], 
                    results['metadatas'][0], 
                    results['distances'][0]
                )):
                    similarity = 1 - distance
                    print(f"\n--- Result {i+1} (Similarity: {similarity:.3f}) ---")
                    print(f"File: {meta.get('file', 'Unknown')}")
                    print(f"Category: {meta.get('category', 'Unknown')}")
                    print(f"Title: {meta.get('title', 'No title')}")
                    print(f"Content: {doc[:150]}...")
            else:
                print("No results found for the query.")
                
        except Exception as e:
            print(f"Search error: {e}")
    
    def show_category_summary(self):
        """Show summary by category"""
        print("\n📊 Category Summary")
        print("=" * 40)
        
        all_docs = self.collection.get(include=["metadatas"])
        
        if not all_docs['metadatas']:
            print("No documents found!")
            return
        
        # Count by category
        categories = {}
        for meta in all_docs['metadatas']:
            category = meta.get('category', 'Unknown')
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        # Display summary
        for category, count in sorted(categories.items()):
            print(f"{category}: {count} chunks")
    
    def show_file_summary(self):
        """Show summary by file"""
        print("\n📁 File Summary")
        print("=" * 40)
        
        all_docs = self.collection.get(include=["metadatas"])
        
        if not all_docs['metadatas']:
            print("No documents found!")
            return
        
        # Count by file
        files = {}
        for meta in all_docs['metadatas']:
            file_name = meta.get('file', 'Unknown')
            if file_name not in files:
                files[file_name] = 0
            files[file_name] += 1
        
        # Display summary
        for file_name, count in sorted(files.items()):
            print(f"{file_name}: {count} chunks")
    
    def export_metadata(self, filename="chromadb_export.json"):
        """Export metadata to JSON file"""
        print(f"\n💾 Exporting metadata to {filename}")
        print("=" * 40)
        
        all_docs = self.collection.get(include=["metadatas", "documents"])
        
        if not all_docs['metadatas']:
            print("No documents to export!")
            return
        
        # Prepare export data
        export_data = []
        for i, (meta, doc) in enumerate(zip(all_docs['metadatas'], all_docs['documents'])):
            export_data.append({
                "id": i,
                "metadata": meta,
                "content_preview": doc[:200] + "..." if len(doc) > 200 else doc
            })
        
        # Write to file
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Exported {len(export_data)} documents to {filename}")
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    def interactive_mode(self):
        """Interactive mode for exploring the database"""
        print("\n🎮 Interactive ChromaDB Explorer")
        print("=" * 40)
        print("Commands:")
        print("  'stats' - Show basic statistics")
        print("  'list' - List all documents")
        print("  'search <query>' - Search for documents")
        print("  'categories' - Show category summary")
        print("  'files' - Show file summary")
        print("  'export' - Export metadata to JSON")
        print("  'quit' - Exit explorer")
        
        while True:
            try:
                command = input("\nEnter command: ").strip().lower()
                
                if command == 'quit':
                    print("Goodbye! 👋")
                    break
                elif command == 'stats':
                    self.show_basic_stats()
                elif command == 'list':
                    self.list_all_documents(limit=10)
                elif command.startswith('search '):
                    query = command[7:]  # Remove 'search ' prefix
                    self.search_documents(query)
                elif command == 'categories':
                    self.show_category_summary()
                elif command == 'files':
                    self.show_file_summary()
                elif command == 'export':
                    self.export_metadata()
                else:
                    print("Unknown command. Available commands: stats, list, search, categories, files, export, quit")
                    
            except KeyboardInterrupt:
                print("\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    """Main function"""
    print("🚀 Simple ChromaDB Viewer")
    print("=" * 40)
    
    try:
        viewer = SimpleChromaDBViewer()
        
        # Show basic info
        viewer.show_basic_stats()
        
        # Start interactive mode
        viewer.interactive_mode()
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure ChromaDB is running and contains data.")

if __name__ == "__main__":
    main()
