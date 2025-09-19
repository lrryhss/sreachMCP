# GraphRAG Chat Interface Implementation Plan

## Overview
Add a GraphRAG-powered chat interface to the research database, enabling users to have conversations with their research data using advanced graph-based retrieval augmented generation.

## Architecture Overview

### 1. Backend Components (FastAPI + PostgreSQL)
- **Vector Database Layer**: Add pgvector extension to PostgreSQL for embeddings
- **Graph Construction**: Build knowledge graph from research results
- **RAG Pipeline**: Implement retrieval and generation with Ollama (Gemma 3:27b)
- **Chat API Endpoints**: New WebSocket/REST endpoints for chat

### 2. Frontend Components (Next.js + React)
- **Chat Interface**: Modern chat UI with message history
- **Context Display**: Show retrieved sources and graph relationships
- **Interactive Features**: Follow-up questions, source citations

## Implementation Steps

### Phase 1: Database Enhancement
1. Enable pgvector extension in PostgreSQL
2. Add embedding columns to research_results and research_artifacts tables
3. Create graph_nodes and graph_edges tables for knowledge graph
4. Add chat_sessions and chat_messages tables

### Phase 2: Backend RAG System
1. Create embedding service using sentence-transformers
2. Build knowledge graph from research data (entities, relationships)
3. Implement hybrid retrieval (vector similarity + graph traversal)
4. Create chat orchestrator with context management
5. Add WebSocket endpoint for real-time chat

### Phase 3: Frontend Chat Interface
1. Create chat component with message bubbles
2. Add source citation system with expandable context
3. Implement typing indicators and streaming responses
4. Add chat history sidebar with session management

### Phase 4: GraphRAG Features
1. Multi-hop reasoning across research results
2. Entity-relationship visualization
3. Query decomposition for complex questions
4. Context-aware follow-up suggestions

## Technical Stack
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Vector DB**: PostgreSQL with pgvector
- **Graph Processing**: NetworkX for Python
- **LLM**: Existing Ollama with Gemma model
- **Frontend**: React with shadcn/ui components
- **Real-time**: WebSockets for chat streaming

## Database Schema

### New Tables

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Graph nodes table
CREATE TABLE graph_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_type VARCHAR(50) NOT NULL,
    node_value TEXT NOT NULL,
    properties JSONB,
    embedding vector(384),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Graph edges table
CREATE TABLE graph_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_node_id UUID REFERENCES graph_nodes(id),
    target_node_id UUID REFERENCES graph_nodes(id),
    edge_type VARCHAR(50) NOT NULL,
    weight FLOAT DEFAULT 1.0,
    properties JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chat sessions table
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    title VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chat messages table
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id),
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add embedding columns to existing tables
ALTER TABLE research_results ADD COLUMN IF NOT EXISTS synthesis_embedding vector(384);
ALTER TABLE research_artifacts ADD COLUMN IF NOT EXISTS content_embedding vector(384);
```

## API Endpoints

### REST Endpoints
- `POST /api/chat/sessions` - Create new chat session
- `GET /api/chat/sessions` - List user's chat sessions
- `GET /api/chat/sessions/{id}/messages` - Get chat history
- `POST /api/chat/messages` - Send chat message
- `GET /api/chat/graph/{task_id}` - Get knowledge graph for research

### WebSocket Endpoint
- `WS /api/chat/stream` - Real-time chat with streaming responses

## Key Features
- Chat with your entire research database
- Automatic source citations with links
- Graph-based context retrieval
- Follow-up question suggestions
- Export chat sessions as reports
- Multi-hop reasoning across research results
- Entity-relationship visualization

## Implementation Priority
1. **Core RAG System** - Basic chat with vector search
2. **Graph Integration** - Add knowledge graph retrieval
3. **UI Enhancement** - Improve chat interface
4. **Advanced Features** - Multi-hop reasoning, visualizations

## Success Metrics
- Response relevance score > 0.8
- Source citation accuracy > 90%
- Response latency < 2 seconds
- User engagement with follow-up questions > 50%