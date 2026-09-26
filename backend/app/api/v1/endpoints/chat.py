from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.agent.router import agent_router
from app.core.database import get_db_session
from app.models.conversation import Conversation, Message, ToolExecutionLog
from app.models.schemas import (
    ChatMessageRequest,
    ChatResponse,
    ConversationSummary,
    MessageItem,
)

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def send_chat_message(
    payload: ChatMessageRequest,
    db: AsyncSession = Depends(get_db_session),
):
    # Step 1: Resolve or create Conversation
    conversation_id = payload.conversation_id
    if conversation_id:
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            # Create if ID not found
            conversation = Conversation(id=conversation_id, title=payload.message[:40])
            db.add(conversation)
            await db.flush()
    else:
        # Generate new conversation with title based on first query
        conversation = Conversation(title=payload.message[:40])
        db.add(conversation)
        await db.flush()
        conversation_id = conversation.id

    # Step 2: Fetch recent message history (last 10 messages)
    history_stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(desc(Message.created_at))
        .limit(10)
    )
    history_res = await db.execute(history_stmt)
    history_messages = list(reversed(history_res.scalars().all()))

    formatted_history = [
        {"role": m.role, "content": m.content or ""} for m in history_messages
    ]

    # Step 3: Run AI agent loop with tool execution
    final_answer, executed_tools = await agent_router.run(
        user_message=payload.message,
        history=formatted_history,
    )

    # Step 4: Persist User Message
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=payload.message,
    )
    db.add(user_msg)

    # Step 5: Persist Assistant Message
    tools_payload = [t.model_dump() for t in executed_tools] if executed_tools else None
    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=final_answer,
        tool_calls=tools_payload,
    )
    db.add(assistant_msg)

    # Step 6: Log tool executions for auditing & metrics
    for tool_detail in executed_tools:
        log_entry = ToolExecutionLog(
            tool_name=tool_detail.tool_name,
            input_args=tool_detail.arguments,
            output_data=tool_detail.result,
            success=tool_detail.success,
            error_message=tool_detail.error,
            execution_time_ms=tool_detail.execution_time_ms,
        )
        db.add(log_entry)

    await db.commit()

    return ChatResponse(
        conversation_id=conversation_id,
        message=final_answer,
        role="assistant",
        tool_calls=executed_tools,
    )


@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(
    limit: int = 30,
    db: AsyncSession = Depends(get_db_session),
):
    stmt = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .order_by(desc(Conversation.updated_at))
        .limit(limit)
    )
    res = await db.execute(stmt)
    conversations = res.scalars().all()

    return [
        ConversationSummary(
            id=c.id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
            message_count=len(c.messages),
        )
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageItem])
async def get_conversation_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    res = await db.execute(stmt)
    messages = res.scalars().all()
    if not messages:
        # Check if conversation exists
        conv_res = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        if not conv_res.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Conversation not found")

    return [
        MessageItem(
            id=m.id,
            role=m.role,
            content=m.content,
            tool_calls=m.tool_calls,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    conv_res = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = conv_res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.delete(conv)
    await db.commit()
    return {"status": "success", "deleted_id": conversation_id}
