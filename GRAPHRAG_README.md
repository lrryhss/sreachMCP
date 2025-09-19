# GraphRAG Chat Interface

## Overview
The GraphRAG Chat Interface enables intelligent conversations with your research database using graph-based retrieval augmented generation. It combines vector similarity search with knowledge graph traversal to provide context-aware responses.

## Features

### 🤖 Intelligent Chat
- **Natural Language Queries**: Ask questions in plain English about your research
- **Context-Aware Responses**: Leverages both recent and historical research data
- **Source Citations**: Every response includes references to the original research

### 🔍 Hybrid Retrieval
- **Vector Search**: Finds semantically similar content using embeddings
- **Graph Traversal**: Discovers connections through knowledge graph relationships
- **Multi-hop Reasoning**: Connects information across multiple research tasks

### 📊 Knowledge Graph
- **Automatic Construction**: Builds graph from research results
- **Entity Extraction**: Identifies key concepts, topics, and findings
- **Relationship Mapping**: Creates connections between related information

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend API   │────▶│   PostgreSQL    │
│   (Next.js)     │     │   (FastAPI)     │     │   + pgvector    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Ollama LLM    │
                    │  (Gemma 3:27b)  │
                    └─────────────────┘
```

## Installation

### Prerequisites
- Docker and Docker Compose
- PostgreSQL with pgvector extension
- Ollama with Gemma model
- Python 3.11+
- Node.js 18+

### Setup Steps

1. **Install Dependencies**
```bash
# Backend dependencies
cd research-agent
pip install -r requirements.txt

# Frontend dependencies
cd ../research-agent-frontend
npm install
```

2. **Initialize Database**
```bash
# Run migration to add GraphRAG tables
cd research-agent
python scripts/init_graphrag.py
```

3. **Start Services**
```bash
# Start all services with Docker Compose
docker-compose up --build -d

# Or run locally for development
# Backend
cd research-agent
uvicorn src.main:app --reload --port 8001

# Frontend
cd research-agent-frontend
npm run dev  # Runs on port 3001
```

4. **Access Chat Interface**
- Open http://localhost:3001/chat
- Sign in with your account
- Start chatting with your research database

## Usage

### Basic Chat
1. Navigate to the Chat interface from the sidebar
2. Type your question in the input field
3. Press Enter or click Send
4. View the response with source citations

### Example Queries
- "What are the main findings from my recent research?"
- "Summarize all research about artificial intelligence"
- "What connections exist between climate change and technology topics?"
- "Find insights about market trends from last month"

### Advanced Features

#### Source Citations
- Click on source badges to expand details
- Click external links to view original research
- Each source shows the research query and creation date

#### Session Management
- Chat sessions are automatically saved
- Create new sessions with the "New Chat" button
- Access chat history from your profile

## API Endpoints

### REST API
- `POST /api/chat/sessions` - Create new session
- `GET /api/chat/sessions` - List sessions
- `POST /api/chat/messages` - Send message
- `GET /api/chat/sessions/{id}/messages` - Get messages
- `DELETE /api/chat/sessions/{id}` - Delete session

### WebSocket
- `WS /api/chat/stream` - Real-time streaming chat

## Technical Details

### Embedding Model
- **Model**: sentence-transformers/all-MiniLM-L6-v2
- **Dimensions**: 384
- **Index Type**: IVFFlat with cosine similarity

### Graph Structure
- **Nodes**: Topics, Findings, Sources, Concepts
- **Edges**: Related_to, Part_of, Causes, References
- **Traversal**: Up to 2 hops for context expansion

### RAG Pipeline
1. **Query Processing**: Embed user query
2. **Retrieval**:
   - Vector search in research results
   - Graph traversal from similar nodes
3. **Ranking**: Combine results with weighted scoring
4. **Generation**: Use Ollama with retrieved context
5. **Response**: Stream or return complete answer

## Performance

### Benchmarks
- Query latency: < 2 seconds
- Embedding generation: ~50ms per text
- Graph traversal: ~100ms for 2 hops
- LLM generation: 1-3 seconds

### Optimization Tips
- Limit context to top 5 results
- Use session caching for repeated queries
- Enable streaming for better UX
- Batch embed during off-peak hours

## Troubleshooting

### Common Issues

1. **pgvector not found**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

2. **Embedding service fails**
```bash
# Check if model downloads correctly
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

3. **Ollama connection error**
```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags
```

4. **Database migration fails**
```bash
# Run migrations manually
psql -U research_user -d research_agent -f sql/migrations/002_add_graphrag_chat.sql
```

## Future Enhancements

### Planned Features
- [ ] Multi-turn conversation memory
- [ ] Custom embedding models
- [ ] Graph visualization interface
- [ ] Export chat as report
- [ ] Voice input/output
- [ ] Fine-tuned domain models

### Experimental Features
- Query decomposition for complex questions
- Automatic follow-up suggestions
- Cross-user knowledge sharing (with permissions)
- Real-time collaborative chat

## Contributing
Contributions are welcome! Please see the main project README for guidelines.

## License
Same as parent project - see main README for details.