"""REST endpoints for conversation management."""

from fastapi import APIRouter, HTTPException
from typing import List
from pathlib import Path
import sys

# Add parent to path for imports
src_dir = Path(__file__).parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from api.schemas import (
    ConversationSummary,
    ConversationDetail,
    ConversationCreate,
    MessageSchema,
    SourceSchema,
)
from api.dependencies import get_chat_service
from datetime import datetime

router = APIRouter()


@router.get("", response_model=List[ConversationSummary])
async def list_conversations():
    """List all saved conversations."""
    chat_service = get_chat_service()
    if not chat_service:
        raise HTTPException(status_code=503, detail="Chat service not available")
    
    conversations = chat_service.list_conversations()
    return [
        ConversationSummary(
            id=c["id"],
            title=c["title"],
            updated_at=datetime.fromisoformat(c["updated_at"]),
            message_count=c["message_count"],
        )
        for c in conversations
    ]


@router.post("", response_model=ConversationDetail)
async def create_conversation(data: ConversationCreate):
    """Create a new conversation."""
    chat_service = get_chat_service()
    if not chat_service:
        raise HTTPException(status_code=503, detail="Chat service not available")
    
    conversation = chat_service.new_conversation(system_prompt=data.system_prompt)
    if data.title and data.title != "New Conversation":
        conversation.title = data.title
    
    chat_service.save_conversation()
    
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        messages=[],
        system_prompt=conversation.system_prompt,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        metadata=conversation.metadata,
    )


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: str):
    """Load a specific conversation."""
    chat_service = get_chat_service()
    if not chat_service:
        raise HTTPException(status_code=503, detail="Chat service not available")
    
    conversation = chat_service.load_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = [
        MessageSchema(
            role=m.role.value,
            content=m.content,
            timestamp=m.timestamp,
            sources=[
                SourceSchema(
                    title=s.title,
                    content=s.content,
                    url=s.url,
                    page=s.page,
                )
                for s in m.sources
            ],
            metadata=m.metadata,
        )
        for m in conversation.messages
    ]
    
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        messages=messages,
        system_prompt=conversation.system_prompt,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        metadata=conversation.metadata,
    )


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    chat_service = get_chat_service()
    if not chat_service:
        raise HTTPException(status_code=503, detail="Chat service not available")
    
    success = chat_service.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"success": True, "message": "Conversation deleted"}
