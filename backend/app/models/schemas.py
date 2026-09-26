from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User's query")
    conversation_id: Optional[str] = Field(
        None, description="Existing conversation ID or empty for a new session"
    )


class ToolCallDetail(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    success: bool = True
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    role: str = "assistant"
    tool_calls: List[ToolCallDetail] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MessageItem(BaseModel):
    id: str
    role: str
    content: Optional[str]
    tool_calls: Optional[List[Dict[str, Any]]] = None
    created_at: datetime


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ToolInfo(BaseModel):
    name: str
    category: str
    description: str
    parameters: Dict[str, Any]
    status: str = "active"
    provider: str


class HealthStatus(BaseModel):
    status: str
    app: str
    version: str
    database: Dict[str, Any]
    cache: Dict[str, Any]
    tools_count: int
