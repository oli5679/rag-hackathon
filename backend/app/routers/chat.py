from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any

from app.dependencies import verify_token
from app.services import chat_service, match_service

router = APIRouter()

# --- Data Models ---

class Message(BaseModel):
    """A single message in a conversation."""
    role: str
    content: str

class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""
    message: str
    conversation_history: List[Message] = []

class ConversationRequest(BaseModel):
    """Request body for the find-matches endpoint."""
    conversation: List[Message]

# --- Endpoints ---

@router.post("/chat")
async def chat(
    request: ChatRequest,
    user: Dict[str, Any] = Depends(verify_token)
) -> Dict[str, Any]:
    """Process a chat message and return assistant response with extracted rules.

    This endpoint is stateless - conversation history comes from the frontend.
    Requires authentication via Bearer token.
    """
    # Convert Pydantic models to dicts for the service layer
    conversation_history: List[Dict[str, str]] = [
        {"role": m.role, "content": m.content} for m in request.conversation_history
    ]

    # Add new message to history for rule extraction
    full_conversation = conversation_history + [{"role": "user", "content": request.message}]

    # Extract rules from full conversation
    rules = await chat_service.extract_rules_from_conversation(full_conversation)

    # Generate response
    assistant_message, search_suggested = await chat_service.generate_response(request.message, conversation_history, rules)

    return {
        "assistantMessage": assistant_message,
        "searchSuggested": search_suggested,
        "hardRules": rules,
    }




@router.post("/find-matches-stream")
async def find_matches_stream(
    request: ConversationRequest,
    user: Dict[str, Any] = Depends(verify_token)
):
    """Streaming RAG pipeline: returns results as they are scored.

    Requires authentication via Bearer token.
    """
    conversation = [
        {"role": m.role, "content": m.content} for m in request.conversation
    ]
    
    return StreamingResponse(
        match_service.stream_matches(conversation),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
