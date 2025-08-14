# RAG Project Learning - AI Assistant with Vector Search

A powerful Retrieval-Augmented Generation (RAG) system built with open-source technologies, featuring an interactive chat interface that can answer questions based on your document knowledge base.

## 🚀 Features

- **Interactive Chat Interface**: Web-based chat UI with streaming responses
- **Vector Database**: ChromaDB for efficient semantic search
- **Document Processing**: Automatic chunking and embedding of documents
- **Semantic Search**: Sentence transformers for intelligent document retrieval
- **Flask Backend**: Lightweight and scalable web framework
- **Open Source**: Built entirely with open-source technologies to avoid vendor lock-in

## 🏗️ Project Structure

```
rag-project-learning/
├── app.py                          # Main Flask application
├── core/                           # Core RAG components
│   ├── __init__.py
│   ├── vector_engine.py           # ChromaDB vector operations
│   ├── chat_engine.py             # Chat logic and RAG pipeline
│   └── document_processor.py      # Document ingestion and processing
├── ingest_documents.py             # Document ingestion script
├── init_vectordb.py               # Vector database initialization
├── legendary-docs/                  # Document storage directory
├── chroma_db/                      # Vector database storage (auto-generated, gitignored)
│   ├── policies/                    # Company policies and guidelines
│   │   └── company-policies.md      # General company policies
│   ├── handbooks/                   # Employee documentation
│   │   └── employee-handbook.md     # Comprehensive employee guide
│   ├── products/                    # Product and service information
│   │   └── product-catalog.md       # AI solutions catalog
│   └── technical/                   # Technical documentation
│       └── technical-specifications.md # System architecture & specs
├── static/                         # Frontend assets
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── chat.js
├── templates/                      # HTML templates
│   └── chat.html
├── test/                          # Test files
│   ├── test_chunking.py
│   ├── test_embeddings.py
│   ├── test_rag_pipeline.py
│   └── test_search.py
├── Pipfile                        # Python dependencies
├── Pipfile.lock                   # Locked dependency versions
└── README.md                      # This file
```

## 🛠️ Prerequisites

- **Python 3.12** (as specified in Pipfile)
- **pipenv** for dependency management
- **Git** for version control

## 📦 Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd rag-project-learning
```

### 2. Install pipenv (if not already installed)

```bash
# On macOS/Linux
pip install pipenv

# On Windows
pip install pipenv
```

### 3. Install Dependencies

```bash
pipenv install
```

This will install all required packages:
- `chromadb` - Vector database for embeddings
- `sentence-transformers` - Text embedding models
- `openai` - OpenAI API integration
- `flask` - Web framework

### 4. Activate Virtual Environment

```bash
pipenv shell
```

## 🚀 Running the Application

### 1. Initialize Vector Database

First, set up the vector database:

```bash
python init_vectordb.py
```

### 2. Ingest Documents (Optional)

If you have documents to process:

```bash
python ingest_documents.py
```

**Note**: The script automatically processes documents from the `legendary-docs/` directory structure. Documents are organized by category:

- **Policies**: Company policies and guidelines
- **Handbooks**: Employee documentation and training materials  
- **Products**: Product catalogs and service information
- **Technical**: Technical specifications and API documentation

The ingestion process will:
- Chunk documents into smaller pieces (500 characters with 100 character overlap)
- Generate embeddings using sentence transformers
- Store in ChromaDB with category metadata
- Provide processing statistics and completion status

### 3. Start the Web Application

```bash
python app.py
```

The application will start on `http://localhost:5000` by default.

### 4. Access the Chat Interface

Open your browser and navigate to `http://localhost:5000` to use the interactive chat interface.

## 🔧 Configuration

### Environment Variables

You can set the following environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key (if using OpenAI models)
- `HF_HUB_DISABLE_TELEMETRY`: Set to '1' to disable HuggingFace telemetry
- `TRANSFORMERS_OFFLINE`: Set to '1' for offline mode

### Document Storage

- Place your documents in the `legendary-docs/` directory
- Documents are automatically chunked and embedded
- Supported formats: Markdown (.md), text files

#### Document Categories

The system organizes documents into logical categories for better retrieval:

- **`policies/`**: Company policies, guidelines, and procedures
- **`handbooks/`**: Employee handbooks, onboarding guides, and training materials
- **`products/`**: Product catalogs, service descriptions, and pricing information
- **`technical/`**: Technical specifications, architecture documents, and API references

Each category helps the RAG system provide more relevant and organized responses to user queries.

## 🧪 Testing

Run the test suite to verify everything is working:

```bash
# Run all tests
python -m pytest test/

# Run specific test files
python test/test_embeddings.py
python test/test_rag_pipeline.py
python test/test_search.py
python test/test_chunking.py
```

## 📚 Usage

### Chat Interface

1. Open the web interface at `http://localhost:5000`
2. Type your question in the chat input
3. The system will search through your organized document knowledge base
4. Receive answers with source citations and confidence scores

#### Example Questions by Category

**Policies & Guidelines:**
- "What is the remote work policy?"
- "How many vacation days do I get?"
- "What is the dress code for client meetings?"

**Employee Information:**
- "How do I onboard as a new employee?"
- "What benefits are available?"
- "What is the performance review process?"

**Products & Services:**
- "What are the pricing tiers for LegendaryAI Core?"
- "What healthcare AI solutions do you offer?"
- "How much does the SDK cost?"

**Technical Details:**
- "What are the system requirements for development?"
- "What API endpoints are available?"
- "How do I integrate with the platform?"

### API Endpoints

- `GET /` - Chat interface
- `POST /api/chat` - Chat with JSON response
- `POST /api/chat/stream` - Streaming chat response

### Example API Usage

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the company policy on remote work?"}'
```

## 🔍 How It Works

1. **Document Processing**: Documents are chunked into smaller pieces and embedded using sentence transformers
2. **Vector Storage**: Embeddings are stored in ChromaDB for fast similarity search
3. **Query Processing**: User questions are embedded and compared against document embeddings
4. **Retrieval**: Most relevant document chunks are retrieved based on semantic similarity
5. **Response Generation**: The system generates answers using retrieved context

### Document Organization Benefits

The categorized document structure provides several advantages:

- **Better Context**: Related documents are grouped together for more coherent responses
- **Faster Retrieval**: Category-based filtering improves search relevance
- **Organized Knowledge**: Users can ask category-specific questions
- **Scalable Structure**: Easy to add new categories and documents
- **Metadata Enrichment**: Category information enhances search accuracy

## 🛠️ Development

### Adding New Features

1. Create feature branches from `main`
2. Add tests for new functionality
3. Update documentation as needed
4. Submit pull requests for review

### Code Structure

- **Core Modules**: Located in `core/` directory
- **Web Interface**: Flask routes in `app.py`
- **Frontend**: Static files in `static/` and templates in `templates/`
- **Tests**: Comprehensive test suite in `test/` directory

## 🐛 Troubleshooting

### Common Issues

1. **ChromaDB Connection Error**: Ensure the `chroma_db` directory exists and has write permissions
2. **Model Download Issues**: Check internet connection for first-time model downloads
3. **Memory Issues**: Large document collections may require more RAM
4. **Port Conflicts**: Change the port in `app.py` if 5000 is already in use

### Debug Mode

Run Flask in debug mode for detailed error messages:

```bash
export FLASK_ENV=development
python app.py
```

## 📄 License

This project is open source. Please check the license file for specific terms.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review existing issues
3. Create a new issue with detailed information

## 🔮 Future Enhancements

- [ ] Support for more document formats (PDF, DOCX)
- [ ] Advanced chunking strategies
- [ ] Multiple embedding models
- [ ] User authentication
- [ ] API rate limiting
- [ ] Docker containerization
- [ ] Kubernetes deployment

---

**Built with ❤️ using open-source technologies**
