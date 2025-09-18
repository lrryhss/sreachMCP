# Research Agent Architecture Overview

## System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Next.js Frontend<br/>React + TypeScript]
        AUTH_UI[NextAuth.js<br/>Authentication]
    end

    subgraph "API Gateway"
        API[FastAPI<br/>REST API]
        AUTH_API[JWT Auth<br/>Middleware]
        WS[WebSocket<br/>SSE Streams]
    end

    subgraph "Business Logic"
        ORCH[Research<br/>Orchestrator]
        REPORT[Report<br/>Generator]
        USER_SVC[User<br/>Service]
        RESEARCH_SVC[Research<br/>Service]
    end

    subgraph "External Services"
        OLLAMA[Ollama<br/>LLM Service]
        MCP[MCP Search<br/>Service]
        FETCH[Content<br/>Fetcher]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL<br/>Primary DB)]
        REDIS[(Redis<br/>Cache)]
        S3[(Object Storage<br/>Future)]
    end

    UI --> AUTH_UI
    AUTH_UI --> API
    UI --> API
    API --> AUTH_API
    API --> WS

    AUTH_API --> USER_SVC
    API --> ORCH
    API --> REPORT
    API --> RESEARCH_SVC

    ORCH --> OLLAMA
    ORCH --> MCP
    ORCH --> FETCH

    USER_SVC --> PG
    RESEARCH_SVC --> PG
    ORCH --> REDIS
    RESEARCH_SVC --> REDIS

    WS -.->|Progress Updates| UI
```

## Component Architecture

```mermaid
graph LR
    subgraph "Frontend Components"
        APP[App Shell]
        AUTH_COMP[Auth Components]
        RESEARCH_COMP[Research UI]
        DASHBOARD[Dashboard]
        HISTORY[History View]
        SHARE[Share Modal]
    end

    subgraph "API Endpoints"
        AUTH_EP[/api/auth/*]
        RESEARCH_EP[/api/research/*]
        USER_EP[/api/user/*]
        SHARE_EP[/api/share/*]
    end

    subgraph "Services"
        AUTH_SVC[AuthService]
        DB_SVC[DatabaseService]
        CACHE_SVC[CacheService]
        SEARCH_SVC[SearchService]
    end

    APP --> AUTH_COMP
    APP --> DASHBOARD
    DASHBOARD --> RESEARCH_COMP
    DASHBOARD --> HISTORY

    AUTH_COMP --> AUTH_EP
    RESEARCH_COMP --> RESEARCH_EP
    HISTORY --> RESEARCH_EP
    SHARE --> SHARE_EP

    AUTH_EP --> AUTH_SVC
    RESEARCH_EP --> DB_SVC
    RESEARCH_EP --> CACHE_SVC
    USER_EP --> DB_SVC
    SHARE_EP --> DB_SVC
```

## Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant O as Orchestrator
    participant DB as Database
    participant R as Redis
    participant LLM as Ollama

    U->>F: Submit Research Query
    F->>A: POST /api/research
    A->>A: Authenticate User
    A->>DB: Create Task Record
    A->>O: Start Research Task
    A-->>F: Return Task ID

    O->>R: Cache Task Status
    O->>LLM: Analyze Query
    O->>O: Search Sources
    O->>O: Fetch Content
    O->>R: Update Progress
    O->>LLM: Synthesize Results
    O->>DB: Save Results
    O->>R: Cache Results

    F->>A: SSE Subscribe
    A->>R: Get Progress
    A-->>F: Stream Updates

    F->>A: GET /api/research/{id}
    A->>R: Check Cache
    alt Cache Hit
        R-->>A: Return Cached
    else Cache Miss
        A->>DB: Fetch from DB
        DB-->>A: Return Data
        A->>R: Update Cache
    end
    A-->>F: Return Results
```

## Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant DB as Database
    participant R as Redis

    U->>F: Login Credentials
    F->>A: POST /api/auth/login
    A->>DB: Verify Credentials
    DB-->>A: User Data
    A->>A: Generate JWT
    A->>R: Store Session
    A-->>F: Return Tokens
    F->>F: Store in Context

    Note over F,A: Subsequent Requests
    F->>A: API Request + JWT
    A->>A: Verify JWT
    A->>R: Check Session
    R-->>A: Valid Session
    A->>A: Process Request
    A-->>F: Return Response
```

## Security Architecture

```mermaid
graph TB
    subgraph "Security Layers"
        HTTPS[HTTPS/TLS]
        CORS[CORS Policy]
        JWT[JWT Tokens]
        HASH[Bcrypt Hashing]
        RATE[Rate Limiting]
        VALID[Input Validation]
    end

    subgraph "Auth Middleware"
        CHECK[Token Validation]
        PERM[Permission Check]
        SESS[Session Validation]
    end

    subgraph "Data Protection"
        ENCRYPT[Encryption at Rest]
        AUDIT[Audit Logging]
        BACKUP[Automated Backups]
    end

    HTTPS --> CORS
    CORS --> JWT
    JWT --> CHECK
    CHECK --> PERM
    PERM --> SESS
    SESS --> VALID

    VALID --> ENCRYPT
    ENCRYPT --> AUDIT
    AUDIT --> BACKUP
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Docker Compose Stack"
        NGINX[Nginx<br/>Reverse Proxy]

        subgraph "Application Containers"
            FRONT[Frontend<br/>Container]
            BACK[Backend<br/>Container]
        end

        subgraph "Data Containers"
            PG_C[PostgreSQL<br/>Container]
            REDIS_C[Redis<br/>Container]
        end

        subgraph "External Services"
            OLLAMA_C[Ollama<br/>Container]
            MCP_C[MCP Search<br/>Container]
        end
    end

    NGINX --> FRONT
    NGINX --> BACK
    BACK --> PG_C
    BACK --> REDIS_C
    BACK --> OLLAMA_C
    BACK --> MCP_C

    subgraph "Volumes"
        PG_VOL[(PostgreSQL<br/>Data)]
        REDIS_VOL[(Redis<br/>Data)]
        LOGS[(Application<br/>Logs)]
    end

    PG_C --> PG_VOL
    REDIS_C --> REDIS_VOL
    BACK --> LOGS
```

## API Structure

### Authentication Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/verify` - Verify email

### Research Endpoints
- `POST /api/research` - Start new research
- `GET /api/research/{id}` - Get research result
- `GET /api/research/history` - List user's research
- `PUT /api/research/{id}` - Update research metadata
- `DELETE /api/research/{id}` - Delete research
- `GET /api/research/{id}/stream` - SSE progress stream

### User Management
- `GET /api/user/profile` - Get user profile
- `PUT /api/user/profile` - Update profile
- `GET /api/user/settings` - Get user settings
- `PUT /api/user/settings` - Update settings
- `DELETE /api/user` - Delete account

### Sharing & Collaboration
- `POST /api/share/{id}` - Create share link
- `GET /api/share/{token}` - Access shared research
- `DELETE /api/share/{id}` - Revoke share
- `GET /api/share/list` - List shared items

## Performance Optimizations

1. **Caching Strategy**
   - Redis for hot data (active tasks, recent results)
   - PostgreSQL JSONB indexes for fast queries
   - Frontend React Query caching

2. **Database Optimization**
   - Connection pooling
   - Prepared statements
   - Batch inserts for artifacts
   - Pagination for large result sets

3. **Async Processing**
   - Background task queue for heavy operations
   - WebSocket/SSE for real-time updates
   - Concurrent source fetching

4. **Resource Management**
   - Rate limiting per user
   - Request timeout controls
   - Memory usage monitoring
   - Automatic cleanup of old data