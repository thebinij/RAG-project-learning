# RAG Project Learning - FastAPI AI Assistant with Vector Search

A powerful Retrieval-Augmented Generation (RAG) system built with **FastAPI** and open-source technologies, featuring an interactive chat interface that can answer questions based on your document knowledge base.

## 🚀 Features

- **FastAPI Backend**: Modern, fast, async-first web framework with automatic API documentation
- **Interactive Chat Interface**: Web-based chat UI with streaming responses
- **Vector Database**: ChromaDB for efficient semantic search
- **Document Processing**: Automatic chunking and embedding of documents
- **Semantic Search**: Sentence transformers for intelligent document retrieval
- **Production Ready**: Structured logging, health checks, Docker deployment
- **Open Source**: Built entirely with open-source technologies to avoid vendor lock-in

## 🏗️ Project Structure

```
rag-project-learning/
├── app/                          # Main FastAPI package
│   ├── __init__.py              # Package initialization
│   ├── app.py                   # FastAPI application definition
│   ├── api/                     # API routers
│   │   ├── v1/                  # API version 1
│   │   │   └── chat.py         # Chat endpoints
│   │   └── visualizer/          # Visualizer endpoints
│   │       └── routes.py
│   ├── core/                    # Core configuration and engines
│   │   ├── config.py            # Settings management
│   │   ├── logging.py           # Logging configuration
│   │   └── engines/             # Core engine modules
│   │       ├── __init__.py
│   │       ├── vector_engine.py # Vector database operations
│   │       ├── chat_engine.py   # RAG chat engine
│   │       └── document_processor.py # Document processing
│   ├── schemas/                 # Pydantic models
│   │   ├── chat.py             # Chat schemas
│   │   └── visualizer.py       # Visualizer schemas
│   ├── services/                # Business logic layer
│   │   ├── vector_service.py    # Vector database operations
│   │   ├── chat_service.py      # Chat/RAG operations
│   │   └── document_service.py  # Document processing
│   └── scripts/                 # Utility scripts
│       ├── ingest_documents.py  # Document ingestion script
│       └── init_vectordb.py    # Vector database initialization
├── static/                      # Frontend assets (CSS, JavaScript)
│   ├── css/
│   └── js/
├── templates/                   # HTML templates
├── knowledge-docs/              # Document storage
├── chroma_db/                   # Vector database storage (auto-generated, gitignored)
├── main.py                      # Entry point (python main.py)
├── start_production.py          # Production entry point
├── Pipfile                      # Python dependencies
├── Pipfile.lock                 # Locked dependency versions
├── Dockerfile                   # Production Docker image
├── docker-compose.yml           # Docker Compose for deployment
├── .dockerignore                # Docker build exclusions
└── README.md                    # Project documentation
```

## 🛠️ Prerequisites

- **Python 3.12** (as specified in Pipfile)
- **pipenv** for dependency management
- **Docker** and **Docker Compose** for deployment (optional)
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
- `fastapi` - Modern, fast web framework
- `uvicorn[standard]` - ASGI server with production features
- `chromadb` - Vector database for embeddings
- `sentence-transformers` - Text embedding models
- `openai` - OpenAI API integration
- `structlog` - Structured logging
- `rich` - Rich console output
- `pydantic` - Data validation and settings management

### 4. Activate Virtual Environment

```bash
pipenv shell
```

## 🚀 Running the Application

### Development Mode

```bash
# Run with auto-reload
python main.py

# Or run as a module
python -m app

# Or use uvicorn directly
uvicorn app.app:app --reload --host 0.0.0.0 --port 5252
```

### Production Mode

```bash
# Use production startup script
python start_production.py

# Or run production module directly
python -m app.production

# Or use uvicorn with production settings
uvicorn app.app:app --host 0.0.0.0 --port 5252 --workers 1 --log-level info
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build and run manually
docker build -t legendarycorp-ai-assistant .
docker run -p 5252:5252 -e OPENAI_API_KEY=your_key legendarycorp-ai-assistant
```

## 🧹 Project Organization

The project follows a clean, modular FastAPI structure:

- **`app/`** - Main application package (Python code only)
  - **`app/app.py`** - FastAPI application definition
  - **`app/api/`** - API endpoints and routers
  - **`app/core/`** - Configuration, logging, and core engines
  - **`app/services/`** - Business logic layer
  - **`app/schemas/`** - Pydantic data models
  - **`app/scripts/`** - Utility scripts for document processing
- **`static/`** - Frontend assets (CSS, JavaScript)
- **`templates/`** - HTML templates

### Running Scripts

```bash
# Document ingestion
cd app/scripts
python ingest_documents.py

# Vector database initialization
python init_vectordb.py
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Application
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=5252

# ChromaDB Visualizer
CHROMA_DB_VISUALIZER=true

# OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE=https://api.openai.com/v1

# HuggingFace
TOKENIZERS_PARALLELISM=false
HF_HUB_DISABLE_TELEMETRY=1
TRANSFORMERS_OFFLINE=0

# Security
CORS_ORIGINS=["*"]
CORS_CREDENTIALS=true
```

### Production Settings

The application automatically detects production vs development environments:

- **Development**: Auto-reload, debug logging, single worker
- **Production**: No reload, structured logging, multiple workers, health checks

## 🌐 Application URLs

Once running, access the application at:

- **Chat Interface**: `http://localhost:5252/` - Main AI chat interface
- **API Documentation**: `http://localhost:5252/docs` - Interactive API docs (Swagger UI)
- **ReDoc Documentation**: `http://localhost:5252/redoc` - Alternative API docs
- **Health Check**: `http://localhost:5252/health` - Application health status
- **ChromaDB Visualizer**: `http://localhost:5252/visualizer` - Database visualization dashboard

## 🐳 Docker Deployment

### Quick Start

```bash
# Start with Docker Compose
docker-compose up --build

# View logs
docker-compose logs -f ai-assistant

# Stop services
docker-compose down
```

### Production Deployment

```bash
# Build production image
docker build -t legendarycorp-ai-assistant:latest .

# Run with production settings
docker run -d \
  --name ai-assistant \
  -p 5252:5252 \
  -e LOG_LEVEL=INFO \
  -e CHROMA_DB_VISUALIZER=true \
  -e OPENAI_API_KEY=your_key \
  -v $(pwd)/chroma_db:/app/chroma_db \
  -v $(pwd)/knowledge-docs:/app/knowledge-docs \
  legendarycorp-ai-assistant:latest
```

### Docker Features

- **Multi-stage build** for optimized image size
- **Non-root user** for security
- **Health checks** for monitoring
- **Volume mounting** for persistent data
- **Environment variable** configuration
- **Production-ready** uvicorn settings

## 📊 Monitoring & Logging

### Structured Logging

The application uses `structlog` for production-grade logging:

```python
import structlog

logger = structlog.get_logger()
logger.info("Application started", port=5252, environment="production")
```

### Health Checks

```bash
# Check application health
curl http://localhost:5252/health

# Response
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Metrics

- Request/response times
- Error rates
- Memory usage
- ChromaDB statistics

## 🧪 Testing

### Run Tests

```bash
# Install dev dependencies
pipenv install --dev

# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov-report=html
```

### API Testing

```bash
# Test chat endpoint
curl -X POST "http://localhost:5252/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the company policy on remote work?"}'

# Test streaming endpoint
curl -X POST "http://localhost:5252/api/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about employee benefits"}'
```

## 🚀 Performance & Scaling

### Async by Default

FastAPI provides excellent performance with async/await:

- **Concurrent requests** handling
- **Non-blocking I/O** operations
- **Efficient streaming** responses
- **WebSocket support** for real-time features

### Production Optimizations

- **Multiple workers** with uvicorn
- **Connection pooling** for databases
- **Caching strategies** for embeddings
- **Load balancing** ready

### Scaling Options

```bash
# Scale with multiple workers
uvicorn app:app --host 0.0.0.0 --port 5252 --workers 4

# Use Gunicorn for more control
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5252
```

## 🔒 Security Features

- **CORS middleware** configuration
- **Input validation** with Pydantic
- **Rate limiting** ready
- **Authentication** ready (can be added)
- **HTTPS** support

## 📈 Production Checklist

- [ ] Set `DEBUG=false`
- [ ] Configure `LOG_LEVEL=INFO` or higher
- [ ] Set proper `CORS_ORIGINS`
- [ ] Use production database
- **Docker**: Use production Dockerfile
- **Monitoring**: Enable health checks
- **Logging**: Configure structured logging
- **Security**: Review CORS and authentication

## 🐛 Troubleshooting

### Common Issues

1. **Port conflicts**: Change port in `.env` or Docker configuration
2. **Memory issues**: Reduce worker count or increase container memory
3. **ChromaDB errors**: Check volume permissions and database initialization
4. **Logging issues**: Verify `LOG_LEVEL` environment variable

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python app.py
```

### Docker Debugging

```bash
# View container logs
docker-compose logs -f ai-assistant

# Access container shell
docker-compose exec ai-assistant bash

# Check container health
docker inspect legendarycorp-ai-assistant
```

## 🔮 Future Enhancements

- [ ] **Authentication & Authorization**
- [ ] **Rate Limiting**
- [ ] **Redis Caching**
- [ ] **Database Migrations**
- [ ] **Kubernetes Deployment**
- [ ] **Prometheus Metrics**
- [ ] **Grafana Dashboards**
- [ ] **CI/CD Pipeline**

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

---

**Built with ❤️ using FastAPI and open-source technologies**
