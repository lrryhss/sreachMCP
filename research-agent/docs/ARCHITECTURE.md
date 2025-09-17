# Research Agent Architecture Documentation

## System Architecture Overview

The Research Agent follows a microservice architecture pattern with async-first design, enabling high concurrency and efficient resource utilization.

## Architectural Patterns

### 1. Hexagonal Architecture (Ports and Adapters)

```mermaid
graph TB
    subgraph "Core Domain"
        UC[Use Cases]
        DM[Domain Models]
        BS[Business Services]
    end

    subgraph "Ports (Interfaces)"
        IP[Input Ports]
        OP[Output Ports]
    end

    subgraph "Adapters (Infrastructure)"
        API[REST API Adapter]
        CLI[CLI Adapter]
        WS[WebSocket Adapter]
        OLL[Ollama Adapter]
        MCP[MCP Adapter]
        WEB[Web Scraper Adapter]
        CACHE[Redis Adapter]
    end

    API --> IP
    CLI --> IP
    WS --> IP

    IP --> UC
    UC --> DM
    UC --> BS
    BS --> OP

    OP --> OLL
    OP --> MCP
    OP --> WEB
    OP --> CACHE

    style UC fill:#ffd700
    style DM fill:#ffd700
    style BS fill:#ffd700
```

### 2. Event-Driven Architecture

```mermaid
graph LR
    subgraph "Event Bus"
        EB[Redis Pub/Sub]
    end

    subgraph "Producers"
        API[API Gateway]
        ORCH[Orchestrator]
    end

    subgraph "Consumers"
        QP[Query Processor]
        SS[Search Service]
        CF[Content Fetcher]
        SYN[Synthesizer]
        RG[Report Generator]
    end

    API -->|research.requested| EB
    ORCH -->|search.needed| EB
    ORCH -->|content.fetch| EB
    ORCH -->|synthesis.start| EB

    EB -->|research.requested| ORCH
    EB -->|search.needed| SS
    EB -->|content.fetch| CF
    EB -->|synthesis.start| SYN
    EB -->|report.generate| RG

    style EB fill:#87CEEB
```

## Component Architecture

### Research Orchestrator Flow

```mermaid
stateDiagram-v2
    [*] --> QueryReceived
    QueryReceived --> QueryAnalysis

    QueryAnalysis --> SearchStrategy
    SearchStrategy --> SearchExecution

    SearchExecution --> URLCollection
    URLCollection --> ContentFetching

    ContentFetching --> ContentExtraction
    ContentExtraction --> QualityCheck

    QualityCheck --> InsufficientContent: < threshold
    QualityCheck --> ContentSynthesis: >= threshold

    InsufficientContent --> SearchStrategy: Retry

    ContentSynthesis --> ReportGeneration
    ReportGeneration --> [*]

    QueryAnalysis --> Failed: Error
    SearchExecution --> Failed: Error
    ContentFetching --> Failed: Error
    ContentSynthesis --> Failed: Error

    Failed --> [*]
```

### Data Flow Architecture

```mermaid
flowchart TB
    subgraph "Input Layer"
        HTTP[HTTP Request]
        WS[WebSocket]
        CLI[CLI Command]
    end

    subgraph "API Gateway"
        FAST[FastAPI]
        VAL[Validation]
        AUTH[Auth Middleware]
        RL[Rate Limiter]
    end

    subgraph "Business Logic"
        ORCH[Orchestrator]
        QP[Query Processor]
        SE[Search Engine]
        FE[Fetch Engine]
        SYN[Synthesis Engine]
    end

    subgraph "External Services"
        OLL[Ollama LLM]
        MCP[MCP Server]
        WEB[Web Sites]
    end

    subgraph "Data Layer"
        REDIS[Redis Cache]
        FS[File System]
    end

    HTTP --> FAST
    WS --> FAST
    CLI --> FAST

    FAST --> VAL
    VAL --> AUTH
    AUTH --> RL
    RL --> ORCH

    ORCH --> QP
    QP --> OLL

    ORCH --> SE
    SE --> MCP

    ORCH --> FE
    FE --> WEB
    FE --> REDIS

    ORCH --> SYN
    SYN --> OLL
    SYN --> REDIS

    ORCH --> FS

    style ORCH fill:#ffd700
    style OLL fill:#90EE90
    style MCP fill:#87CEEB
```

## Sequence Diagrams

### Complete Research Flow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Orchestrator
    participant QueryProcessor
    participant Ollama
    participant SearchService
    participant MCPServer
    participant ContentFetcher
    participant WebSite
    participant Synthesizer
    participant ReportGen
    participant Redis

    User->>API: POST /research {query}
    API->>API: Validate request
    API->>Orchestrator: Start research task
    API-->>User: 202 {task_id}

    activate Orchestrator
    Orchestrator->>Redis: Create task entry
    Orchestrator->>QueryProcessor: Analyze query

    activate QueryProcessor
    QueryProcessor->>Ollama: Extract intent & entities
    Ollama-->>QueryProcessor: Analysis result
    QueryProcessor->>Ollama: Generate search strategies
    Ollama-->>QueryProcessor: Search terms
    QueryProcessor-->>Orchestrator: Processed query
    deactivate QueryProcessor

    loop For each search strategy
        Orchestrator->>SearchService: Execute search
        activate SearchService
        SearchService->>MCPServer: Search request
        MCPServer->>MCPServer: Query SearXNG
        MCPServer-->>SearchService: Search results
        SearchService-->>Orchestrator: URLs list
        deactivate SearchService
    end

    Orchestrator->>ContentFetcher: Fetch URLs batch
    activate ContentFetcher

    par Parallel Fetching
        ContentFetcher->>WebSite: GET content 1
        and
        ContentFetcher->>WebSite: GET content 2
        and
        ContentFetcher->>WebSite: GET content N
    end

    ContentFetcher->>ContentFetcher: Extract & clean
    ContentFetcher->>Redis: Cache content
    ContentFetcher-->>Orchestrator: Processed content
    deactivate ContentFetcher

    Orchestrator->>Synthesizer: Synthesize findings
    activate Synthesizer
    Synthesizer->>Redis: Get cached content
    Synthesizer->>Ollama: Summarize content
    Ollama-->>Synthesizer: Summaries
    Synthesizer->>Ollama: Generate synthesis
    Ollama-->>Synthesizer: Final analysis
    Synthesizer-->>Orchestrator: Research findings
    deactivate Synthesizer

    Orchestrator->>ReportGen: Generate report
    activate ReportGen
    ReportGen->>ReportGen: Format HTML
    ReportGen->>Redis: Cache report
    ReportGen-->>Orchestrator: Report ready
    deactivate ReportGen

    Orchestrator->>Redis: Update task complete
    deactivate Orchestrator

    User->>API: GET /research/{task_id}/report
    API->>Redis: Get report
    Redis-->>API: Cached report
    API-->>User: HTML report
```

### Real-time Streaming Flow

```mermaid
sequenceDiagram
    participant User
    participant SSE
    participant Orchestrator
    participant EventBus

    User->>SSE: GET /research/{task_id}/stream
    SSE->>EventBus: Subscribe to task events

    loop Research Progress
        Orchestrator->>EventBus: Publish progress event
        EventBus->>SSE: Forward event
        SSE-->>User: event: progress {data}
    end

    Orchestrator->>EventBus: Publish complete event
    EventBus->>SSE: Forward complete
    SSE-->>User: event: complete {report_url}
    SSE->>SSE: Close connection
```

## Deployment Architecture

### Container Architecture

```mermaid
graph TB
    subgraph "Docker Network"
        subgraph "Research Agent Container"
            APP[FastAPI App]
            WORK[Celery Workers]
        end

        subgraph "Redis Container"
            CACHE[Cache Store]
            QUEUE[Task Queue]
            PUBSUB[Event Bus]
        end

        subgraph "Host Network"
            OLLAMA[Ollama Service]
            MCP[MCP Server Container]
        end
    end

    subgraph "External"
        SEARX[SearXNG Container]
        WEB[Internet]
    end

    APP --> CACHE
    APP --> QUEUE
    APP --> PUBSUB

    WORK --> QUEUE
    WORK --> CACHE

    APP --> OLLAMA
    WORK --> OLLAMA

    APP --> MCP
    WORK --> MCP

    MCP --> SEARX
    WORK --> WEB

    style APP fill:#ffd700
    style OLLAMA fill:#90EE90
    style MCP fill:#87CEEB
```

### Kubernetes Architecture (Future)

```mermaid
graph TB
    subgraph "Kubernetes Cluster"
        subgraph "Namespace: research-agent"
            subgraph "Deployments"
                API[API Deployment<br/>3 replicas]
                WORK[Worker Deployment<br/>5 replicas]
            end

            subgraph "Services"
                APISVC[API Service<br/>LoadBalancer]
                REDISSVC[Redis Service<br/>ClusterIP]
            end

            subgraph "StatefulSets"
                REDIS[Redis StatefulSet<br/>1 replica]
            end

            subgraph "ConfigMaps & Secrets"
                CM[ConfigMap]
                SEC[Secrets]
            end
        end

        subgraph "Ingress"
            ING[Ingress Controller]
        end
    end

    subgraph "External Services"
        OLL[Ollama Node]
        MCP[MCP Server]
    end

    ING --> APISVC
    APISVC --> API
    API --> REDISSVC
    WORK --> REDISSVC
    REDISSVC --> REDIS

    API --> CM
    WORK --> CM
    API --> SEC
    WORK --> SEC

    API --> OLL
    WORK --> OLL
    API --> MCP
    WORK --> MCP

    style API fill:#ffd700
```

## Scalability Architecture

### Horizontal Scaling Pattern

```mermaid
graph LR
    subgraph "Load Balancer"
        LB[Nginx/HAProxy]
    end

    subgraph "API Layer"
        API1[API Instance 1]
        API2[API Instance 2]
        API3[API Instance 3]
    end

    subgraph "Worker Layer"
        W1[Worker 1<br/>Content Fetch]
        W2[Worker 2<br/>Content Fetch]
        W3[Worker 3<br/>Synthesis]
        W4[Worker 4<br/>Synthesis]
        W5[Worker 5<br/>Report Gen]
    end

    subgraph "Data Layer"
        RED1[Redis Primary]
        RED2[Redis Replica]
    end

    LB --> API1
    LB --> API2
    LB --> API3

    API1 --> RED1
    API2 --> RED1
    API3 --> RED1

    W1 --> RED1
    W2 --> RED1
    W3 --> RED1
    W4 --> RED1
    W5 --> RED1

    RED1 --> RED2

    style LB fill:#87CEEB
    style RED1 fill:#ff9999
```

## Security Architecture

### Security Layers

```mermaid
graph TB
    subgraph "External"
        USER[User]
        ATK[Attacker]
    end

    subgraph "Security Layers"
        subgraph "Layer 1: Network"
            FW[Firewall]
            DDoS[DDoS Protection]
        end

        subgraph "Layer 2: Application"
            WAF[Web App Firewall]
            RL[Rate Limiter]
        end

        subgraph "Layer 3: Authentication"
            AUTH[Auth Middleware]
            TOKEN[Token Validation]
        end

        subgraph "Layer 4: Authorization"
            RBAC[Role-Based Access]
            PERM[Permissions]
        end

        subgraph "Layer 5: Data"
            ENC[Encryption at Rest]
            VALID[Input Validation]
            SAN[Output Sanitization]
        end
    end

    subgraph "Application"
        APP[Research Agent]
    end

    USER --> FW
    ATK --> FW
    FW --> DDoS
    DDoS --> WAF
    WAF --> RL
    RL --> AUTH
    AUTH --> TOKEN
    TOKEN --> RBAC
    RBAC --> PERM
    PERM --> VALID
    VALID --> APP
    APP --> SAN
    APP --> ENC

    style ATK fill:#ff6666
    style APP fill:#90EE90
```

## Caching Architecture

### Multi-Level Cache Strategy

```mermaid
graph TD
    subgraph "L1 Cache"
        MEM[In-Memory<br/>FastAPI Cache<br/>TTL: 60s]
    end

    subgraph "L2 Cache"
        REDIS[Redis Cache<br/>TTL: 1 hour]
    end

    subgraph "L3 Cache"
        FS[File System<br/>Reports Archive<br/>TTL: 7 days]
    end

    REQ[Request] --> MEM
    MEM -->|Hit| RESP1[Response]
    MEM -->|Miss| REDIS
    REDIS -->|Hit| MEM
    MEM --> RESP2[Response]
    REDIS -->|Miss| FS
    FS -->|Hit| REDIS
    REDIS --> MEM
    MEM --> RESP3[Response]
    FS -->|Miss| COMPUTE[Compute]
    COMPUTE --> FS
    FS --> REDIS
    REDIS --> MEM
    MEM --> RESP4[Response]

    style MEM fill:#ffeb3b
    style REDIS fill:#ff9800
    style FS fill:#4caf50
```

## Error Handling Architecture

### Circuit Breaker Pattern

```mermaid
stateDiagram-v2
    [*] --> Closed
    Closed --> Open: Failure threshold reached
    Open --> HalfOpen: After timeout
    HalfOpen --> Closed: Success
    HalfOpen --> Open: Failure
    Closed --> Closed: Success

    state Closed {
        [*] --> Monitoring
        Monitoring --> Monitoring: Success
        Monitoring --> CountingFailures: Failure
        CountingFailures --> Monitoring: < Threshold
    }

    state Open {
        [*] --> RejectingRequests
        RejectingRequests --> WaitingTimeout
    }

    state HalfOpen {
        [*] --> TestingService
        TestingService --> Evaluating
    }
```

## Monitoring Architecture

### Observability Stack

```mermaid
graph TB
    subgraph "Application"
        APP[Research Agent]
        METRICS[Metrics Exporter]
        LOGS[Log Aggregator]
        TRACES[Trace Collector]
    end

    subgraph "Monitoring Stack"
        PROM[Prometheus]
        LOKI[Loki]
        TEMPO[Tempo]
        GRAF[Grafana]
    end

    subgraph "Alerting"
        AM[AlertManager]
        SLACK[Slack]
        EMAIL[Email]
    end

    APP --> METRICS
    APP --> LOGS
    APP --> TRACES

    METRICS --> PROM
    LOGS --> LOKI
    TRACES --> TEMPO

    PROM --> GRAF
    LOKI --> GRAF
    TEMPO --> GRAF

    PROM --> AM
    AM --> SLACK
    AM --> EMAIL

    style GRAF fill:#ffd700
    style PROM fill:#ff6b35
    style LOKI fill:#4ecdc4
    style TEMPO fill:#95e1d3
```

## Performance Optimization Patterns

### Async Processing Pipeline

```mermaid
graph LR
    subgraph "Async Pipeline"
        Q1[Query Queue]
        Q2[Search Queue]
        Q3[Fetch Queue]
        Q4[Synthesis Queue]
        Q5[Report Queue]
    end

    subgraph "Workers"
        W1[Query Workers<br/>Pool: 2]
        W2[Search Workers<br/>Pool: 3]
        W3[Fetch Workers<br/>Pool: 5]
        W4[Synthesis Workers<br/>Pool: 2]
        W5[Report Workers<br/>Pool: 2]
    end

    REQ[Request] --> Q1
    Q1 --> W1
    W1 --> Q2
    Q2 --> W2
    W2 --> Q3
    Q3 --> W3
    W3 --> Q4
    Q4 --> W4
    W4 --> Q5
    Q5 --> W5
    W5 --> RESULT[Result]

    style Q3 fill:#ff9999
    style W3 fill:#ff9999
```

## Database Schema (Redis)

### Key Structure

```mermaid
graph TD
    subgraph "Redis Key Namespace"
        subgraph "Tasks"
            T1[task:res_xxx:status]
            T2[task:res_xxx:progress]
            T3[task:res_xxx:result]
        end

        subgraph "Cache"
            C1[cache:search:hash]
            C2[cache:content:url_hash]
            C3[cache:report:task_id]
        end

        subgraph "Sessions"
            S1[session:user_id:data]
            S2[session:user_id:tasks]
        end

        subgraph "Metrics"
            M1[metrics:requests:daily]
            M2[metrics:latency:histogram]
            M3[metrics:errors:counter]
        end

        subgraph "Pub/Sub Channels"
            P1[channel:task:task_id]
            P2[channel:events:global]
        end
    end

    style T1 fill:#87CEEB
    style C1 fill:#90EE90
    style S1 fill:#ffd700
    style M1 fill:#ff9999
    style P1 fill:#dda0dd
```

## Technology Decisions

### Technology Stack Rationale

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Language** | Python 3.11+ | Async support, rich ecosystem, LLM libraries |
| **Framework** | FastAPI | High performance, automatic OpenAPI docs, async native |
| **LLM Client** | Ollama Python | Local processing, privacy, no API costs |
| **Task Queue** | Celery + Redis | Mature, scalable, monitoring tools |
| **Cache** | Redis | Fast, pub/sub support, persistence options |
| **Content Extraction** | Trafilatura + BeautifulSoup | Best accuracy, fallback options |
| **PDF Processing** | PyPDF2 | Pure Python, no system dependencies |
| **HTML Reports** | Jinja2 | Fast, secure, familiar syntax |
| **Monitoring** | Prometheus + Grafana | Industry standard, rich dashboards |
| **Container** | Docker | Consistent deployment, easy scaling |

## Architectural Principles

1. **Separation of Concerns**: Each component has a single, well-defined responsibility
2. **Async-First**: All I/O operations are asynchronous for maximum concurrency
3. **Fail-Fast**: Quick failure detection and graceful degradation
4. **Cache Everything**: Multi-level caching for performance
5. **Observability**: Comprehensive logging, metrics, and tracing
6. **Security by Design**: Defense in depth, input validation, output sanitization
7. **Scalability**: Horizontal scaling through stateless components
8. **Modularity**: Loosely coupled components with clear interfaces

## Future Architecture Considerations

### Planned Enhancements

1. **GraphQL API**: Alternative to REST for flexible querying
2. **gRPC Services**: Internal service communication
3. **Event Sourcing**: Complete audit trail of research tasks
4. **CQRS Pattern**: Separate read/write models for optimization
5. **Federated Search**: Distributed search across multiple instances
6. **ML Pipeline**: Custom model training for domain-specific research
7. **Knowledge Graph**: Persistent knowledge base from research
8. **Multi-tenancy**: Isolated environments for different users/organizations