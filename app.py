"""
AI Assistant - Interactive RAG Chat Interface with ChromaDB Visualization
"""

from flask import Flask, render_template, request, jsonify, Response, stream_with_context, redirect
import os
import sys
from datetime import datetime
import json
import time
from collections import Counter
from dotenv import load_dotenv

load_dotenv()
# Add core modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from core.vector_engine import VectorEngine
from core.chat_engine import ChatEngine
from core.document_processor import DocumentProcessor

app = Flask(__name__)

# Configuration
CHROMA_DB_VISUALIZER_ENABLED = os.getenv('CHROMA_DB_VISUALIZER', 'false').lower() == 'true'

# Initialize RAG components
print("\n" + "="*60)
print("🚀 Starting LegendaryCorp AI Assistant")
if CHROMA_DB_VISUALIZER_ENABLED:
    print("   with ChromaDB Visualizer (ENABLED)")
else:
    print("   ChromaDB Visualizer (DISABLED)")
print("="*60)
print("\n[INIT] Loading RAG components...")

vector_engine = VectorEngine()
print("[INIT] Vector engine ready")

chat_engine = ChatEngine(vector_engine)
print("[INIT] Chat engine ready")

doc_processor = DocumentProcessor(vector_engine)
print("[INIT] Document processor ready")

# Initialize ChromaDB viewer only if enabled
if CHROMA_DB_VISUALIZER_ENABLED:
    print("[INIT] Initializing ChromaDB viewer...")
    class ChromaDBWebViewer:
        def __init__(self, vector_engine_instance):
            """Initialize the web viewer using existing VectorEngine's ChromaDB client"""
            try:
                # Use the existing ChromaDB client from VectorEngine
                self.client = vector_engine_instance.client
                self.collection = vector_engine_instance.collection
                print("[INIT] ChromaDB viewer ready (using existing client)")
            except Exception as e:
                print(f"[WARNING] ChromaDB viewer initialization failed: {e}")
                self.client = None
                self.collection = None
        
        def get_database_stats(self):
            """Get comprehensive database statistics"""
            try:
                if not self.collection:
                    return {'error': 'ChromaDB not available'}
                    
                total_chunks = self.collection.count()
                
                if total_chunks == 0:
                    return {
                        'total_chunks': 0,
                        'categories': {},
                        'files': {},
                        'avg_chunk_size': 0,
                        'metadata_keys': []
                    }
                
                # Get all documents with metadata
                all_docs = self.collection.get(include=["metadatas", "documents"])
                
                # Category distribution
                categories = [meta.get('category', 'Unknown') for meta in all_docs['metadatas']]
                category_counts = Counter(categories)
                
                # File distribution
                files = [meta.get('file', 'Unknown') for meta in all_docs['metadatas']]
                file_counts = Counter(files)
                
                # Average chunk size
                chunk_lengths = [len(doc) for doc in all_docs['documents']]
                avg_chunk_size = sum(chunk_lengths) / len(chunk_lengths) if chunk_lengths else 0
                
                # Metadata keys
                metadata_keys = list(all_docs['metadatas'][0].keys()) if all_docs['metadatas'] else []
                
                return {
                    'total_chunks': total_chunks,
                    'categories': dict(category_counts),
                    'files': dict(file_counts),
                    'avg_chunk_size': round(avg_chunk_size, 1),
                    'metadata_keys': metadata_keys
                }
            except Exception as e:
                return {'error': str(e)}
        
        def search_documents(self, query, limit=10):
            """Search for documents using semantic search"""
            try:
                if not self.collection:
                    return {'error': 'ChromaDB not available'}
                    
                results = self.collection.query(
                    query_texts=[query],
                    n_results=limit,
                    include=["documents", "metadatas", "distances"]
                )
                
                if results['metadatas'] and len(results['metadatas'][0]) > 0:
                    search_results = []
                    for i, (doc, meta, distance) in enumerate(zip(
                        results['documents'][0], 
                        results['metadatas'][0], 
                        results['distances'][0]
                    )):
                        similarity = 1 - distance
                        search_results.append({
                            'id': i,
                            'content': doc,
                            'metadata': meta,
                            'similarity': round(similarity, 3),
                            'content_preview': doc[:200] + "..." if len(doc) > 200 else doc
                        })
                    return search_results
                else:
                    return []
            except Exception as e:
                return {'error': str(e)}
        
        def get_all_documents(self, limit=None, offset=0):
            """Get all documents with pagination"""
            try:
                if not self.collection:
                    return {'error': 'ChromaDB not available'}
                    
                all_docs = self.collection.get(include=["metadatas", "documents"])
                
                if not all_docs['metadatas']:
                    return []
                
                documents = []
                for i, (meta, doc) in enumerate(zip(all_docs['metadatas'], all_docs['documents'])):
                    if limit and i >= limit:
                        break
                    if i < offset:
                        continue
                        
                    documents.append({
                        'id': i,
                        'content': doc,
                        'metadata': meta,
                        'content_preview': doc[:150] + "..." if len(doc) > 150 else doc
                    })
                
                return documents
            except Exception as e:
                return {'error': str(e)}
        
        def get_documents_by_category(self, category):
            """Get documents filtered by category"""
            try:
                if not self.collection:
                    return {'error': 'ChromaDB not available'}
                    
                all_docs = self.collection.get(include=["metadatas", "documents"])
                
                if not all_docs['metadatas']:
                    return []
                
                documents = []
                for i, (meta, doc) in enumerate(zip(all_docs['metadatas'], all_docs['documents'])):
                    if meta.get('category') == category:
                        documents.append({
                            'id': i,
                            'content': doc,
                            'metadata': meta,
                            'content_preview': doc[:150] + "..." if len(doc) > 150 else doc
                        })
                
                return documents
            except Exception as e:
                return {'error': str(e)}

    # Initialize the viewer with the existing VectorEngine instance
    viewer = ChromaDBWebViewer(vector_engine)
    print("[INIT] ChromaDB viewer ready")
else:
    print("[INIT] ChromaDB visualizer disabled by environment variable")
    viewer = None

print("[INIT] All components ready!")

# ===== CHAT INTERFACE ROUTES =====

@app.route('/')
def index():
    """Render the chat interface"""
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get response from RAG system
        response = chat_engine.get_response(user_message)
        
        return jsonify({
            'response': response['answer'],
            'sources': response['sources'],
            'confidence': response['confidence'],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """Handle chat messages with streaming response"""
    def generate():
        try:
            data = request.json
            user_message = data.get('message', '')
            
            if not user_message:
                yield f"data: {json.dumps({'error': 'No message provided'})}\n\n"
                return
            
            # Send initial event
            yield f"data: {json.dumps({'event': 'start'})}\n\n"
            
            # Get response from RAG system
            response = chat_engine.get_response(user_message)
            
            # Stream the response character by character to preserve markdown formatting
            response_text = response['answer']
            for char in response_text:
                time.sleep(0.01)  # Smaller delay for smoother streaming
                yield f"data: {json.dumps({'event': 'token', 'content': char})}\n\n"
            
            # Send sources at the end
            yield f"data: {json.dumps({'event': 'sources', 'sources': response['sources'], 'confidence': response['confidence']})}\n\n"
            
            # Send completion event
            yield f"data: {json.dumps({'event': 'done'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'error': str(e)})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/api/status', methods=['GET'])
def status():
    """Get system status"""
    try:
        stats = vector_engine.get_stats()
        return jsonify({
            'status': 'operational',
            'documents': stats['total_documents'],
            'chunks': stats['total_chunks'],
            'last_updated': stats['last_updated'],
            'chroma_visualizer_enabled': CHROMA_DB_VISUALIZER_ENABLED
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ===== CHROMADB VISUALIZER ROUTES (Conditional) =====

def require_visualizer_enabled(f):
    """Decorator to check if visualizer is enabled"""
    def decorated_function(*args, **kwargs):
        if not CHROMA_DB_VISUALIZER_ENABLED:
            return jsonify({'error': 'ChromaDB Visualizer is disabled. Set CHROMA_DB_VISUALIZER=true to enable.'}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/visualizer')
@require_visualizer_enabled
def visualizer_dashboard():
    """Main ChromaDB visualization dashboard"""
    stats = viewer.get_database_stats()
    return render_template('dashboard.html', stats=stats)

@app.route('/visualizer/documents')
@require_visualizer_enabled
def visualizer_documents():
    """Documents page for ChromaDB visualizer"""
    return render_template('documents.html')

@app.route('/visualizer/search')
@require_visualizer_enabled
def visualizer_search():
    """Search page for ChromaDB visualizer"""
    return render_template('search.html')

@app.route('/visualizer/explore')
@require_visualizer_enabled
def visualizer_explore():
    """Explore page for ChromaDB visualizer"""
    return render_template('explore.html')

@app.route('/api/visualizer/stats')
@require_visualizer_enabled
def api_visualizer_stats():
    """API endpoint for ChromaDB database statistics"""
    stats = viewer.get_database_stats()
    return jsonify(stats)

@app.route('/api/visualizer/search')
@require_visualizer_enabled
def api_visualizer_search():
    """API endpoint for document search in ChromaDB"""
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
    if not query:
        return jsonify([])
    
    results = viewer.search_documents(query, limit)
    return jsonify(results)

@app.route('/api/visualizer/documents')
@require_visualizer_enabled
def api_visualizer_documents():
    """API endpoint for getting documents from ChromaDB"""
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', 0, type=int)
    category = request.args.get('category')
    
    if category:
        documents = viewer.get_documents_by_category(category)
    else:
        documents = viewer.get_all_documents(limit, offset)
    
    return jsonify(documents)

# ===== NAVIGATION ROUTES =====

@app.route('/chat')
def chat_interface():
    """Redirect to chat interface"""
    return redirect('/')

@app.route('/help')
def help_page():
    """Help and documentation page"""
    return render_template('help.html')

# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    if CHROMA_DB_VISUALIZER_ENABLED and request.path.startswith('/visualizer'):
        return jsonify({'error': 'Visualizer route not found'}), 404
    return jsonify({'error': 'Route not found'}), 404

@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors (visualizer disabled)"""
    return jsonify({'error': 'ChromaDB Visualizer is disabled. Set CHROMA_DB_VISUALIZER=true to enable.'}), 403

if __name__ == '__main__':
    # Initialize database with documents on first run
    if not vector_engine.is_initialized():
        print("First run detected. Processing LegendaryCorp documents...")
        doc_processor.process_all_documents()
        print("Document processing complete!")
    
    print("\n" + "="*60)
    print("🌐 Application URLs:")
    print("   Chat Interface:     http://localhost:5252/")
    if CHROMA_DB_VISUALIZER_ENABLED:
        print("   ChromaDB Visualizer: http://localhost:5252/visualizer")
        print("   Documents Browser:   http://localhost:5252/visualizer/documents")
        print("   Search Interface:    http://localhost:5252/visualizer/search")
        print("   Data Explorer:       http://localhost:5252/visualizer/explore")
    else:
        print("   ChromaDB Visualizer: DISABLED (set CHROMA_DB_VISUALIZER=true to enable)")
    print("   Help:                 http://localhost:5252/help")
    print("="*60)
    
    # Run the app
    app.run(host='0.0.0.0', port=5252, debug=True)