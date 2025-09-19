"""Research management API endpoints"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from structlog import get_logger

from ..database import get_db
from ..database.models import User, ResearchTask, ResearchResult, TaskStatus
from ..services.database_service import DatabaseService
from ..api.auth import get_current_user
from ..agent.orchestrator import ResearchOrchestrator
from ..services.report_generator import ReportGenerator
from ..services.embedding_service import get_embedding_service

logger = get_logger()

router = APIRouter(prefix="/api/research", tags=["Research"])


# Request/Response models
class ResearchCreateRequest(BaseModel):
    """Create research request"""
    query: str = Field(..., min_length=5, max_length=1000)
    depth: str = Field("standard", pattern="^(quick|standard|comprehensive)$")
    max_sources: int = Field(20, ge=5, le=50)
    options: Optional[Dict[str, Any]] = None


class ResearchResponse(BaseModel):
    """Research task response"""
    id: str
    task_id: str
    query: str
    status: str
    depth: str
    max_sources: int
    progress: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]


class ResearchResultResponse(BaseModel):
    """Research result response"""
    task_id: str
    query: str
    status: str
    completed_at: datetime
    sources_used: int
    synthesis: Dict[str, Any]
    sources: List[Dict[str, Any]]
    query_analysis: Optional[Dict[str, Any]]
    detailed_analysis: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]


class ResearchListResponse(BaseModel):
    """List of research tasks"""
    tasks: List[ResearchResponse]
    total: int
    limit: int
    offset: int


class ResearchUpdateRequest(BaseModel):
    """Update research metadata"""
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    is_archived: Optional[bool] = None


# Global instances (these should be injected properly in production)
orchestrator: Optional[ResearchOrchestrator] = None
report_generator: Optional[ReportGenerator] = None


def get_orchestrator():
    """Get orchestrator instance"""
    global orchestrator
    if not orchestrator:
        from ..agent.orchestrator import ResearchOrchestrator
        orchestrator = ResearchOrchestrator()
    return orchestrator


def get_report_generator():
    """Get report generator instance"""
    global report_generator
    if not report_generator:
        from ..services.report_generator import ReportGenerator
        report_generator = ReportGenerator()
    return report_generator


@router.post("", response_model=ResearchResponse, status_code=status.HTTP_201_CREATED)
async def create_research(
    request: ResearchCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Create a new research task"""
    db_service = DatabaseService(session)

    # Generate task ID
    import uuid
    task_id = f"res_{uuid.uuid4().hex[:12]}"

    # Create task in database
    task = await db_service.tasks.create(
        task_id=task_id,
        query=request.query,
        user_id=current_user.id,
        depth=request.depth,
        max_sources=request.max_sources,
        options=request.options or {}
    )
    await db_service.commit()

    # Start research in background
    background_tasks.add_task(
        execute_research,
        task_id=task_id,
        task_db_id=task.id,
        query=request.query,
        depth=request.depth,
        max_sources=request.max_sources,
        options=request.options,
        user_id=current_user.id
    )

    logger.info(
        "Research task created",
        task_id=task_id,
        user_id=str(current_user.id),
        query=request.query
    )

    return ResearchResponse(
        id=str(task.id),
        task_id=task.task_id,
        query=task.query,
        status=task.status,
        depth=task.depth,
        max_sources=task.max_sources,
        progress=task.progress,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        error_message=task.error_message
    )


async def execute_research(
    task_id: str,
    task_db_id: UUID,
    query: str,
    depth: str,
    max_sources: int,
    options: Optional[Dict[str, Any]],
    user_id: UUID
):
    """Execute research task in background"""
    from ..database.connection import db_manager

    async with db_manager.get_session() as session:
        db_service = DatabaseService(session)

        try:
            # Get orchestrator
            orch = get_orchestrator()

            # Execute research
            results = await orch.execute_research(
                query=query,
                depth=depth,
                max_sources=max_sources,
                options=options,
                task_id=task_id
            )

            # Generate embeddings for GraphRAG
            synthesis_embedding = None
            query_embedding = None

            try:
                embedding_service = await get_embedding_service()

                # Generate query embedding
                query_embedding_array = await embedding_service.embed_text(query)
                query_embedding = query_embedding_array.tolist()

                # Generate synthesis embedding from combined synthesis content
                synthesis_data = results.get("synthesis", {})
                synthesis_text = ""

                # Extract text from synthesis for embedding
                if isinstance(synthesis_data, dict):
                    if "executive_summary" in synthesis_data:
                        synthesis_text += str(synthesis_data["executive_summary"]) + " "
                    if "key_findings" in synthesis_data:
                        findings = synthesis_data["key_findings"]
                        if isinstance(findings, list):
                            synthesis_text += " ".join(str(f) for f in findings) + " "
                        else:
                            synthesis_text += str(findings) + " "
                    if "conclusion" in synthesis_data:
                        synthesis_text += str(synthesis_data["conclusion"])

                if synthesis_text.strip():
                    synthesis_embedding_array = await embedding_service.embed_text(synthesis_text.strip())
                    synthesis_embedding = synthesis_embedding_array.tolist()

                logger.info(
                    "Generated embeddings for research",
                    task_id=task_id,
                    query_embedding_dim=len(query_embedding) if query_embedding else 0,
                    synthesis_embedding_dim=len(synthesis_embedding) if synthesis_embedding else 0
                )

            except Exception as e:
                logger.warning(
                    "Failed to generate embeddings",
                    task_id=task_id,
                    error=str(e)
                )

            # Save results to database with embeddings
            await db_service.results.create(
                task_id=task_db_id,
                synthesis=results.get("synthesis", {}),
                sources=results.get("sources", []),
                query_analysis=results.get("query_analysis"),
                detailed_analysis=results.get("detailed_analysis"),
                metadata=results.get("metadata"),
                featured_media=results.get("featured_media"),
                sources_used=results.get("sources_used", 0),
                synthesis_embedding=synthesis_embedding,
                query_embedding=query_embedding
            )

            # Update task status
            await db_service.tasks.update_status(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                progress=100
            )

            await db_service.commit()

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

            # Update task status to failed
            await db_service.tasks.update_status(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error_message=str(e)
            )
            await db_service.commit()


@router.get("/history", response_model=ResearchListResponse)
async def get_research_history(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, pattern="^(pending|completed|failed|cancelled)$"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get user's research history"""
    db_service = DatabaseService(session)

    # Get user's tasks
    tasks = await db_service.tasks.get_user_tasks(
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )

    # Get total count
    count_result = await session.execute(
        select(ResearchTask).where(ResearchTask.user_id == current_user.id)
    )
    total = len(count_result.scalars().all())

    # Convert to response format
    task_responses = [
        ResearchResponse(
            id=str(task.id),
            task_id=task.task_id,
            query=task.query,
            status=task.status.value,
            depth=task.depth.value,
            max_sources=task.max_sources,
            progress=task.progress,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            error_message=task.error_message
        )
        for task in tasks
    ]

    return ResearchListResponse(
        tasks=task_responses,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/{task_id}", response_model=ResearchResponse)
async def get_research_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get a specific research task"""
    db_service = DatabaseService(session)

    # Get task
    task = await db_service.tasks.get_by_task_id(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research task not found"
        )

    # Check ownership
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return ResearchResponse(
        id=str(task.id),
        task_id=task.task_id,
        query=task.query,
        status=task.status,
        depth=task.depth,
        max_sources=task.max_sources,
        progress=task.progress,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        error_message=task.error_message
    )


@router.get("/{task_id}/status", response_model=ResearchResponse)
async def get_research_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get research task status"""
    return await get_research_task(task_id, current_user, session)


@router.get("/{task_id}/result", response_model=ResearchResultResponse)
async def get_research_result(
    task_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get research results"""
    db_service = DatabaseService(session)

    # Get task
    task = await db_service.tasks.get_by_task_id(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research task not found"
        )

    # Check ownership
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Check if completed
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task is {task.status.value}, not completed"
        )

    # Get result
    if not task.result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Results not found"
        )

    return ResearchResultResponse(
        task_id=task.task_id,
        query=task.query,
        status=task.status.value,
        completed_at=task.completed_at,
        sources_used=task.result.sources_used or 0,
        synthesis=task.result.synthesis,
        sources=task.result.sources,
        query_analysis=task.result.query_analysis,
        detailed_analysis=task.result.detailed_analysis,
        metadata=task.result.result_metadata if isinstance(task.result.result_metadata, dict) else None
    )


@router.get("/{task_id}/report")
async def get_research_report(
    task_id: str,
    format: str = Query("html", pattern="^(html|markdown|json)$"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get formatted research report"""
    db_service = DatabaseService(session)

    # Get task with result
    task = await db_service.tasks.get_by_task_id(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research task not found"
        )

    # Check ownership
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Check if completed
    if task.status != TaskStatus.COMPLETED or not task.result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Research not completed"
        )

    # Generate report
    report_gen = get_report_generator()

    # Build results dict
    results = {
        "task_id": task.task_id,
        "query": task.query,
        "synthesis": task.result.synthesis,
        "sources": task.result.sources,
        "query_analysis": task.result.query_analysis,
        "detailed_analysis": task.result.detailed_analysis,
        "metadata": task.result.metadata,
        "sources_used": task.result.sources_used
    }

    if format == "json":
        from fastapi.responses import JSONResponse
        return JSONResponse(content=results)
    elif format == "markdown":
        from fastapi.responses import Response
        report = report_gen.generate_markdown_report(results)
        return Response(content=report, media_type="text/markdown")
    else:  # html
        from fastapi.responses import HTMLResponse
        report = report_gen.generate_html_report(results)
        return HTMLResponse(content=report)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_research(
    task_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Delete a research task"""
    db_service = DatabaseService(session)

    # Get task
    task = await db_service.tasks.get_by_task_id(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research task not found"
        )

    # Check ownership
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Delete task (cascade will delete results and artifacts)
    await session.delete(task)
    await db_service.commit()

    logger.info(
        "Research task deleted",
        task_id=task_id,
        user_id=str(current_user.id)
    )


@router.post("/{task_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_research(
    task_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Cancel a pending research task"""
    db_service = DatabaseService(session)

    # Get task
    task = await db_service.tasks.get_by_task_id(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research task not found"
        )

    # Check ownership
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Check if can be cancelled
    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel task in {task.status.value} status"
        )

    # Update status
    await db_service.tasks.update_status(
        task_id=task_id,
        status=TaskStatus.CANCELLED
    )
    await db_service.commit()

    # Try to cancel in orchestrator
    orch = get_orchestrator()
    await orch.cancel_task(task_id)

    logger.info(
        "Research task cancelled",
        task_id=task_id,
        user_id=str(current_user.id)
    )


@router.get("/search", response_model=ResearchListResponse)
async def search_research(
    q: str = Query(..., min_length=3, max_length=100),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Search user's research history"""
    db_service = DatabaseService(session)

    # Search tasks
    tasks = await db_service.tasks.search(
        query=q,
        user_id=current_user.id,
        limit=limit
    )

    # Convert to response format
    task_responses = [
        ResearchResponse(
            id=str(task.id),
            task_id=task.task_id,
            query=task.query,
            status=task.status.value,
            depth=task.depth.value,
            max_sources=task.max_sources,
            progress=task.progress,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            error_message=task.error_message
        )
        for task in tasks
    ]

    return ResearchListResponse(
        tasks=task_responses,
        total=len(task_responses),
        limit=limit,
        offset=0
    )