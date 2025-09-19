"""Chat API endpoints for GraphRAG-powered conversations"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from structlog import get_logger

from ..database import get_db
from ..database.models import User, ResearchTask
from ..services.rag_service import RAGService
from ..services.database_service import DatabaseService
from ..api.auth import get_current_user
from ..clients.ollama_client import OllamaClient
import os

logger = get_logger()

router = APIRouter(prefix="/api/chat", tags=["Chat"])

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:2b")


# Request/Response models
class ChatSessionCreate(BaseModel):
    """Create chat session request"""
    title: Optional[str] = Field(None, max_length=255)
    context: Optional[Dict[str, Any]] = None


class ChatSessionResponse(BaseModel):
    """Chat session response"""
    id: str
    user_id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_activity: datetime
    message_count: Optional[int] = 0


class ChatMessageCreate(BaseModel):
    """Create chat message request"""
    session_id: str
    content: str = Field(..., min_length=1, max_length=5000)
    stream: bool = Field(False)


class ChatMessageResponse(BaseModel):
    """Chat message response"""
    id: str
    session_id: str
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = []
    created_at: datetime


class ChatSearchRequest(BaseModel):
    """Search chat history request"""
    query: str = Field(..., min_length=1, max_length=100)
    session_id: Optional[str] = None
    limit: int = Field(10, ge=1, le=50)


# Define SQLAlchemy models for chat tables
from sqlalchemy import Column, String, Text, ForeignKey, TIMESTAMP, update
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.sql import func
from ..database.models import Base


class ChatSession(Base):
    """Chat session model"""
    __tablename__ = "chat_sessions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(String(255))
    context = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_activity = Column(TIMESTAMP(timezone=True), server_default=func.now())


class ChatMessage(Base):
    """Chat message model"""
    __tablename__ = "chat_messages"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    retrieved_context = Column(JSONB, default={})
    sources = Column(JSONB, default=[])
    message_metadata = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


# WebSocket manager
class ConnectionManager:
    """Manager for WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info("WebSocket connected", user_id=user_id)

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info("WebSocket disconnected", user_id=user_id)

    async def send_message(self, user_id: str, message: Dict[str, Any]):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_json(message)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    request: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Create a new chat session"""
    # Create session
    chat_session = ChatSession(
        user_id=current_user.id,
        title=request.title or f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        context=request.context or {}
    )
    session.add(chat_session)
    await session.commit()
    await session.refresh(chat_session)

    logger.info(
        "Chat session created",
        session_id=str(chat_session.id),
        user_id=str(current_user.id)
    )

    return ChatSessionResponse(
        id=str(chat_session.id),
        user_id=str(chat_session.user_id),
        title=chat_session.title,
        created_at=chat_session.created_at,
        updated_at=chat_session.updated_at,
        last_activity=chat_session.last_activity,
        message_count=0
    )


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get user's chat sessions"""
    # Get sessions
    result = await session.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(desc(ChatSession.last_activity))
        .limit(limit)
        .offset(offset)
    )
    sessions = result.scalars().all()

    # Get message counts
    response_sessions = []
    for chat_session in sessions:
        message_count_result = await session.execute(
            select(func.count(ChatMessage.id))
            .where(ChatMessage.session_id == chat_session.id)
        )
        message_count = message_count_result.scalar() or 0

        response_sessions.append(ChatSessionResponse(
            id=str(chat_session.id),
            user_id=str(chat_session.user_id),
            title=chat_session.title,
            created_at=chat_session.created_at,
            updated_at=chat_session.updated_at,
            last_activity=chat_session.last_activity,
            message_count=message_count
        ))

    return response_sessions


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get messages from a chat session"""
    # Verify session ownership
    chat_session_result = await session.execute(
        select(ChatSession)
        .where(and_(
            ChatSession.id == UUID(session_id),
            ChatSession.user_id == current_user.id
        ))
    )
    chat_session = chat_session_result.scalar_one_or_none()

    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    # Get messages
    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == UUID(session_id))
        .order_by(ChatMessage.created_at)
        .limit(limit)
        .offset(offset)
    )
    messages = result.scalars().all()

    return [
        ChatMessageResponse(
            id=str(message.id),
            session_id=str(message.session_id),
            role=message.role,
            content=message.content,
            sources=message.sources or [],
            created_at=message.created_at
        )
        for message in messages
    ]


@router.post("/messages", response_model=ChatMessageResponse)
async def send_chat_message(
    request: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Send a chat message and get response"""
    # Verify session ownership
    chat_session_result = await session.execute(
        select(ChatSession)
        .where(and_(
            ChatSession.id == UUID(request.session_id),
            ChatSession.user_id == current_user.id
        ))
    )
    chat_session = chat_session_result.scalar_one_or_none()

    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    # Save user message
    user_message = ChatMessage(
        session_id=UUID(request.session_id),
        role="user",
        content=request.content
    )
    session.add(user_message)

    # Get conversation history
    history_result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == UUID(request.session_id))
        .order_by(desc(ChatMessage.created_at))
        .limit(10)
    )
    history = history_result.scalars().all()
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in reversed(history)
    ]

    # Process with RAG service
    ollama_client = OllamaClient(OLLAMA_BASE_URL, OLLAMA_MODEL)
    rag_service = RAGService(session, ollama_client)
    result = await rag_service.process_chat_message(
        message=request.content,
        user_id=current_user.id,
        session_id=UUID(request.session_id),
        conversation_history=conversation_history,  # Pass the history!
        stream=request.stream
    )

    # Handle response
    if request.stream:
        # For streaming, return immediately with session info
        # Actual streaming happens via WebSocket
        return ChatMessageResponse(
            id=str(user_message.id),
            session_id=request.session_id,
            role="assistant",
            content="[Streaming response...]",
            sources=result["context"]["sources"],
            created_at=datetime.utcnow()
        )
    else:
        # Save assistant response
        assistant_message = ChatMessage(
            session_id=UUID(request.session_id),
            role="assistant",
            content=result["response"]["content"],
            retrieved_context=result["context"],
            sources=result["context"]["sources"]
        )
        session.add(assistant_message)

        # Update session activity
        await session.execute(
            update(ChatSession)
            .where(ChatSession.id == UUID(request.session_id))
            .values(last_activity=func.now())
        )

        await session.commit()
        await session.refresh(assistant_message)

        return ChatMessageResponse(
            id=str(assistant_message.id),
            session_id=str(assistant_message.session_id),
            role=assistant_message.role,
            content=assistant_message.content,
            sources=assistant_message.sources,
            created_at=assistant_message.created_at
        )


@router.websocket("/stream")
async def websocket_chat(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for streaming chat"""
    # TODO: Validate token and get user
    # For now, using a simplified approach
    user_id = "websocket_user"  # Should be extracted from token

    await manager.connect(websocket, user_id)

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()

            message = data.get("message", "")
            session_id = data.get("session_id")

            if not message:
                continue

            # Send typing indicator
            await manager.send_message(user_id, {
                "type": "typing",
                "status": True
            })

            # Process with RAG service
            rag_service = RAGService(db, OllamaClient())
            result = await rag_service.process_chat_message(
                message=message,
                user_id=UUID(user_id) if user_id else None,  # Fix this with proper auth
                session_id=UUID(session_id) if session_id else None,
                stream=True
            )

            # Stream response
            if result["response"]["type"] == "stream":
                async for chunk in result["response"]["generator"]:
                    await manager.send_message(user_id, {
                        "type": "stream",
                        "content": chunk
                    })

            # Send sources
            await manager.send_message(user_id, {
                "type": "sources",
                "sources": result["context"]["sources"]
            })

            # Send completion
            await manager.send_message(user_id, {
                "type": "complete",
                "status": True
            })

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info("WebSocket disconnected", user_id=user_id)
    except Exception as e:
        logger.error("WebSocket error", error=str(e), user_id=user_id)
        manager.disconnect(user_id)


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Delete a chat session"""
    # Verify ownership and delete
    chat_session_result = await session.execute(
        select(ChatSession)
        .where(and_(
            ChatSession.id == UUID(session_id),
            ChatSession.user_id == current_user.id
        ))
    )
    chat_session = chat_session_result.scalar_one_or_none()

    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    await session.delete(chat_session)
    await session.commit()

    logger.info(
        "Chat session deleted",
        session_id=session_id,
        user_id=str(current_user.id)
    )

    return {"status": "deleted"}


@router.post("/search", response_model=List[ChatMessageResponse])
async def search_chat_history(
    request: ChatSearchRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Search chat history"""
    # Build search query
    query = select(ChatMessage).join(
        ChatSession,
        ChatMessage.session_id == ChatSession.id
    ).where(
        and_(
            ChatSession.user_id == current_user.id,
            ChatMessage.content.ilike(f"%{request.query}%")
        )
    )

    if request.session_id:
        query = query.where(ChatMessage.session_id == UUID(request.session_id))

    query = query.order_by(desc(ChatMessage.created_at)).limit(request.limit)

    # Execute search
    result = await session.execute(query)
    messages = result.scalars().all()

    return [
        ChatMessageResponse(
            id=str(message.id),
            session_id=str(message.session_id),
            role=message.role,
            content=message.content,
            sources=message.sources or [],
            created_at=message.created_at
        )
        for message in messages
    ]