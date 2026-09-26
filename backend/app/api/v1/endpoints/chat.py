from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.agent.router import agent_router
from app.core.database import get_db_session
from app.core.rate_limiter import check_chat_rate_limit
from app.core.security import AuthenticatedUser, get_current_user
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
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    # Step 1: Rate limiting per user/session
    await check_chat_rate_limit(request, user.user_id)

    # Step 2: Resolve or create Conversation with strict user ownership
    conversation_id = payload.conversation_id
    if conversation_id:
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            # Check ownership
            if conversation.user_id != user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: You do not own this conversation.",
                )
        else:
            # Create if ID not found, assigned to this user
            conversation = Conversation(
                id=conversation_id,
                user_id=user.user_id,
                title=payload.message[:40],
            )
            db.add(conversation)
            await db.flush()
    else:
        # Generate new conversation owned by current user
        conversation = Conversation(
            user_id=user.user_id,
            title=payload.message[:40],
        )
        db.add(conversation)
        await db.flush()
        conversation_id = conversation.id

    # Step 3: Fetch recent message history (last 10 messages)
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

    # Step 4: Run AI agent loop with tool execution
    final_answer, executed_tools = await agent_router.run(
        user_message=payload.message,
        history=formatted_history,
    )

    # Step 5: Persist User Message
    user_msg = Message(
        conversation_id=conversation_id,
        user_id=user.user_id,
        role="user",
        content=payload.message,
    )
    db.add(user_msg)

    # Step 6: Persist Assistant Message
    tools_payload = [t.model_dump() for t in executed_tools] if executed_tools else None
    assistant_msg = Message(
        conversation_id=conversation_id,
        user_id=user.user_id,
        role="assistant",
        content=final_answer,
        tool_calls=tools_payload,
    )
    db.add(assistant_msg)

    # Step 7: Log tool executions for auditing & metrics
    for tool_detail in executed_tools:
        log_entry = ToolExecutionLog(
            conversation_id=conversation_id,
            user_id=user.user_id,
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
    user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List conversations strictly belonging to the authenticated user/session."""
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == user.user_id)
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
    user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Retrieve messages with strict ownership verification."""
    # Step 1: Verify conversation exists and belongs to current user
    conv_res = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = conv_res.scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    if conv.user_id != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have access to this conversation.",
        )

    # Step 2: Fetch conversation messages
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    res = await db.execute(stmt)
    messages = res.scalars().all()

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
    user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete a conversation with strict ownership verification."""
    conv_res = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = conv_res.scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    if conv.user_id != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You cannot delete another user's conversation.",
        )

    await db.delete(conv)
    await db.commit()
    return {"status": "success", "deleted_id": conversation_id}
