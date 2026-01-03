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
from utils.config import get_config

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
                # Allow per-request max_tokens override (ideal for future UX)
                request_max_tokens = message.get("max_tokens")
                
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
                    search_metadata = None
                    
                    # Add user message first
                    chat_service.current_conversation.add_message(
                        MessageRole.USER, content
                    )
                    
                    # Prepare messages
                    messages, sources_data, search_metadata = chat_service._prepare_messages(content)
                    sources = [
                        {
                            "title": s.title,
                            "content": s.content,
                            "url": s.url,
                            "page": s.page
                        }
                        for s in sources_data
                    ]
                    
                    # Send search metadata if available (before streaming starts)
                    if search_metadata:
                        await websocket.send_json({
                            "type": "search_info",
                            "query": search_metadata["query"],
                            "results": search_metadata["results"]
                        })
                    
                    # Stream tokens
                    llm_service = get_llm_service()
                    config = get_config()
                    
                    # Determine max_tokens: request override > config > default
                    max_tokens = request_max_tokens or config.max_tokens
                    max_tokens = max(128, min(max_tokens, 4096))  # Clamp to valid range
                    
                    # Apply smart capping based on remaining context
                    safe_max_tokens = chat_service.get_safe_max_tokens(max_tokens)
                    
                    for token in llm_service.generate_stream(
                        messages=messages,
                        max_tokens=safe_max_tokens,
                        temperature=config.temperature,
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
                    
                    # Check if context needs summarization (>70%)
                    usage = chat_service.get_context_usage()
                    needs_auto_summary = usage.get("needs_summary", False)
                    
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
                        "conversation_id": chat_service.current_conversation.id,
                        "context_usage": usage
                    })
                    
                    # Auto-summarize if needed
                    if needs_auto_summary:
                        await websocket.send_json({
                            "type": "summarizing",
                            "status": "summarizing",
                            "message": "Summarizing context..."
                        })
                        
                        try:
                            summary = chat_service.summarize_context(keep_recent_messages=4)
                            new_usage = chat_service.get_context_usage()
                            
                            await websocket.send_json({
                                "type": "summary_complete",
                                "success": True,
                                "context_usage": new_usage,
                                "message": f"Context summarized! Now at {new_usage['usage_percent']}%"
                            })
                        except Exception as e:
                            await websocket.send_json({
                                "type": "summary_complete",
                                "success": False,
                                "message": f"Failed to summarize: {str(e)}"
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
