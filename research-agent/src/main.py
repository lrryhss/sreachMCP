"""FastAPI main application for Research Agent"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvloop
from structlog import get_logger

from .config import settings
from .agent.orchestrator import ResearchOrchestrator
from .services.report_generator import ReportGenerator

# Use uvloop for better async performance
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logger = get_logger()

# Global instances
orchestrator: Optional[ResearchOrchestrator] = None
report_generator: Optional[ReportGenerator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global orchestrator, report_generator
    
    logger.info("Starting Research Agent", version="1.0.0")
    
    # Initialize components
    orchestrator = ResearchOrchestrator()
    report_generator = ReportGenerator()
    
    # Health check for dependencies
    async with orchestrator.ollama_client as ollama:
        if not await ollama.health_check():
            logger.warning("Ollama not available", model=settings.ollama.model)
    
    if not await orchestrator.search_client.health_check():
        logger.warning("MCP Search server not available")
    
    yield
    
    logger.info("Shutting down Research Agent")


# Create FastAPI app
app = FastAPI(
    title="Research Agent API",
    description="AI-powered research agent with web search and content synthesis",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure from settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ResearchRequest(BaseModel):
    """Research request model"""
    query: str = Field(..., description="Research query or question")
    depth: str = Field("standard", description="Research depth: quick, standard, comprehensive")
    max_sources: int = Field(20, ge=5, le=50, description="Maximum number of sources")
    output_format: str = Field("html", description="Output format: html, json, markdown")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")


class ResearchResponse(BaseModel):
    """Research response model"""
    task_id: str
    status: str
    message: str
    result_url: Optional[str] = None


class TaskStatusResponse(BaseModel):
    """Task status response"""
    task_id: str
    status: str
    progress: Dict[str, Any]
    query: str
    created_at: str
    updated_at: Optional[str]
    error: Optional[str]


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Research Agent",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "research": "/api/research",
            "status": "/api/research/{task_id}/status",
            "result": "/api/research/{task_id}/result",
            "cancel": "/api/research/{task_id}/cancel",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Check Ollama
    try:
        async with orchestrator.ollama_client as ollama:
            ollama_healthy = await ollama.health_check()
            health_status["checks"]["ollama"] = {
                "status": "healthy" if ollama_healthy else "unhealthy",
                "model": settings.ollama.model
            }
    except Exception as e:
        health_status["checks"]["ollama"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check MCP Search
    try:
        mcp_healthy = await orchestrator.search_client.health_check()
        health_status["checks"]["mcp_search"] = {
            "status": "healthy" if mcp_healthy else "unhealthy"
        }
    except Exception as e:
        health_status["checks"]["mcp_search"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Overall health
    all_healthy = all(
        check.get("status") == "healthy"
        for check in health_status["checks"].values()
    )
    
    if not all_healthy:
        health_status["status"] = "degraded"
    
    return health_status


@app.post("/api/research", response_model=ResearchResponse)
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks
):
    """Start a new research task"""
    try:
        # Generate task ID
        task_id = f"res_{uuid.uuid4().hex[:12]}"

        # Initialize task in orchestrator
        from .agent.orchestrator import ResearchStatus
        orchestrator.tasks[task_id] = {
            "id": task_id,
            "query": request.query,
            "status": ResearchStatus.PENDING,
            "progress": 0,
            "created_at": datetime.utcnow().isoformat(),
            "steps_completed": [],
            "current_step": "initializing"
        }

        logger.info(
            "Starting research task",
            task_id=task_id,
            query=request.query,
            depth=request.depth
        )

        # Start research in background
        background_tasks.add_task(
            run_research,
            task_id=task_id,
            query=request.query,
            depth=request.depth,
            max_sources=request.max_sources,
            output_format=request.output_format,
            options=request.options
        )
        
        return ResearchResponse(
            task_id=task_id,
            status="started",
            message="Research task started",
            result_url=f"/api/research/{task_id}/result"
        )
    
    except Exception as e:
        logger.error("Failed to start research", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


async def run_research(
    task_id: str,
    query: str,
    depth: str,
    max_sources: int,
    output_format: str,
    options: Optional[Dict[str, Any]]
):
    """Run research task (background)"""
    try:
        # Execute research with task_id
        results = await orchestrator.execute_research(
            query=query,
            depth=depth,
            max_sources=max_sources,
            options=options,
            task_id=task_id
        )
        
        # Store formatted report based on output format
        if output_format == "json":
            report = report_generator.generate_json_report(results)
        elif output_format == "markdown":
            report = report_generator.generate_markdown_report(results)
        else:  # html
            report = report_generator.generate_html_report(results)
        
        # Store report in task results
        orchestrator.tasks[task_id]["report"] = report
        orchestrator.tasks[task_id]["output_format"] = output_format
        
        logger.info(
            "Research completed",
            task_id=task_id,
            sources_used=results.get("sources_used", 0)
        )
    
    except Exception as e:
        logger.error(
            "Research task failed",
            task_id=task_id,
            error=str(e)
        )
        if task_id in orchestrator.tasks:
            orchestrator.tasks[task_id]["error"] = str(e)
            orchestrator.tasks[task_id]["status"] = "failed"


@app.get("/api/research/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get research task status"""
    status = await orchestrator.get_task_status(task_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskStatusResponse(**status)


@app.get("/api/research/{task_id}/result")
async def get_task_result(task_id: str, format: Optional[str] = None):
    """Get research task results"""
    if task_id not in orchestrator.tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = orchestrator.tasks[task_id]
    
    # Check if task is complete
    if task["status"].value != "completed":
        return JSONResponse(
            status_code=202,
            content={
                "status": task["status"].value,
                "message": "Task still in progress",
                "progress": task["progress"]
            }
        )
    
    # Get report
    report = task.get("report")
    if not report:
        results = task.get("results")
        if not results:
            raise HTTPException(status_code=500, detail="No results available")
        
        # Generate report if not cached
        if format == "json" or task.get("output_format") == "json":
            report = report_generator.generate_json_report(results)
        elif format == "markdown" or task.get("output_format") == "markdown":
            report = report_generator.generate_markdown_report(results)
        else:
            report = report_generator.generate_html_report(results)
    
    # Return appropriate response type
    if format == "json" or task.get("output_format") == "json":
        return JSONResponse(content=results if format == "json" else report)
    elif format == "markdown" or task.get("output_format") == "markdown":
        return Response(content=report, media_type="text/markdown")
    else:
        return HTMLResponse(content=report)


@app.delete("/api/research/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a research task"""
    cancelled = await orchestrator.cancel_task(task_id)
    
    if not cancelled:
        raise HTTPException(
            status_code=404,
            detail="Task not found or already completed"
        )
    
    return {"status": "cancelled", "task_id": task_id}


@app.get("/api/research/tasks")
async def list_tasks(limit: int = 10, offset: int = 0):
    """List all research tasks"""
    tasks = []
    
    # Get all tasks (sorted by creation time, newest first)
    all_task_ids = sorted(
        orchestrator.tasks.keys(),
        key=lambda x: orchestrator.tasks[x].get("created_at", ""),
        reverse=True
    )
    
    # Apply pagination
    paginated_ids = all_task_ids[offset:offset + limit]
    
    for task_id in paginated_ids:
        task = orchestrator.tasks[task_id]
        tasks.append({
            "task_id": task_id,
            "query": task["query"],
            "status": task["status"].value if hasattr(task["status"], "value") else task["status"],
            "progress": task["progress"],
            "created_at": task["created_at"],
            "updated_at": task.get("updated_at")
        })
    
    return {
        "tasks": tasks,
        "total": len(all_task_ids),
        "limit": limit,
        "offset": offset
    }


@app.get("/api/research/{task_id}/stream")
async def stream_task_progress(task_id: str):
    """Stream task progress updates via Server-Sent Events"""
    if task_id not in orchestrator.tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    async def event_generator():
        """Generate SSE events"""
        last_progress = -1
        last_status = None
        
        while True:
            task = orchestrator.tasks.get(task_id)
            if not task:
                yield f"data: {{\"error\": \"Task not found\"}}\n\n"
                break
            
            current_progress = task["progress"]
            current_status = task["status"]
            
            # Send update if progress changed
            if current_progress != last_progress or current_status != last_status:
                event_data = {
                    "task_id": task_id,
                    "status": current_status.value if hasattr(current_status, "value") else current_status,
                    "progress": current_progress,
                    "current_step": task.get("current_step", ""),
                    "steps_completed": task.get("steps_completed", [])
                }
                
                yield f"data: {JSONResponse(content=event_data).body.decode()}\n\n"
                
                last_progress = current_progress
                last_status = current_status
            
            # Check if task is complete
            if current_status in ["completed", "failed", "cancelled"]:
                yield f"data: {{\"status\": \"{current_status}\", \"complete\": true}}\n\n"
                break
            
            # Wait before next check
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )