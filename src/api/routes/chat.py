"""WebSocket chat endpoint for streaming responses."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional
import json
import asyncio
from pathlib import Path
import sys

# Add parent to path for imports
src_dir = Path(__file__).parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from api.dependencies import get_chat_service, get_llm_service
from models.message import MessageRole

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_json(self, client_id: str, data: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(data)


manager = ConnectionManager()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for streaming chat.
    
    Protocol:
    - Client sends: {"type": "message", "content": "...", "conversation_id": "..."}
    - Client sends: {"type": "cancel"} to stop generation
    - Server sends: {"type": "token", "content": "..."} for each token
    - Server sends: {"type": "complete", "message": {...}, "sources": [...]}
    - Server sends: {"type": "error", "message": "..."}
    - Server sends: {"type": "status", "generating": true/false}
    """
    # Generate unique client ID
    client_id = str(id(websocket))
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
                continue
            
            msg_type = message.get("type")
            
            if msg_type == "cancel":
                # Cancel ongoing generation
                llm_service = get_llm_service()
                if llm_service:
                    llm_service.cancel_generation()
                await websocket.send_json({
                    "type": "status",
                    "generating": False
                })
                continue
            
            if msg_type == "message":
                content = message.get("content", "").strip()
                conversation_id = message.get("conversation_id")
                
                if not content:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Empty message"
                    })
                    continue
                
                chat_service = get_chat_service()
                if not chat_service:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Chat service not available"
                    })
                    continue
                
                # Load or create conversation
                if conversation_id:
                    # Load existing conversation
                    chat_service.load_conversation(conversation_id)
                else:
                    # No conversation_id means new chat - always create fresh
                    chat_service.new_conversation()
                
                # Send status: generating
                await websocket.send_json({
                    "type": "status",
                    "generating": True
                })
                
                # Stream response
                try:
                    # Run streaming in thread to not block
                    response_text = ""
                    sources = []
                    
                    # Add user message first
                    chat_service.current_conversation.add_message(
                        MessageRole.USER, content
                    )
                    
                    # Prepare messages
                    messages, sources_data = chat_service._prepare_messages(content)
                    sources = [
                        {
                            "title": s.title,
                            "content": s.content,
                            "url": s.url,
                            "page": s.page
                        }
                        for s in sources_data
                    ]
                    
                    # Stream tokens
                    llm_service = get_llm_service()
                    for token in llm_service.generate_stream(
                        messages=messages,
                        max_tokens=1024,
                        temperature=0.7,
                    ):
                        response_text += token
                        await websocket.send_json({
                            "type": "token",
                            "content": token
                        })
                        # Small delay to prevent flooding
                        await asyncio.sleep(0.01)
                    
                    # Add assistant message to conversation
                    from models.message import Source
                    assistant_sources = [
                        Source(
                            title=s["title"],
                            content=s["content"],
                            url=s.get("url"),
                            page=s.get("page"),
                        )
                        for s in sources
                    ]
                    
                    assistant_message = chat_service.current_conversation.add_message(
                        MessageRole.ASSISTANT,
                        response_text,
                        sources=assistant_sources,
                    )
                    
                    # Save conversation
                    chat_service.save_conversation()
                    
                    # Send complete message
                    await websocket.send_json({
                        "type": "complete",
                        "message": {
                            "role": "assistant",
                            "content": response_text,
                            "timestamp": assistant_message.timestamp.isoformat(),
                            "sources": sources,
                            "metadata": {}
                        },
                        "sources": sources,
                        "conversation_id": chat_service.current_conversation.id
                    })
                    
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
                
                finally:
                    # Send status: not generating
                    await websocket.send_json({
                        "type": "status",
                        "generating": False
                    })
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        manager.disconnect(client_id)
        print(f"WebSocket error: {e}")
