"""SpareRoom Assistant API - FastAPI backend for room finding with RAG."""

import asyncio
import json
from datetime import date
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from clients import openai_client
from clients.redis_client import redis_client

load_dotenv()

app = FastAPI(title="SpareRoom Assistant API")

# CORS configuration
ALLOWED_ORIGINS: list[str] = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SYSTEM_PROMPT = """You are a helpful SpareRoom assistant helping users find rooms to rent in London.

Today's date: {today}

Your goal is to understand what the user is looking for by asking clarifying questions. Key topics to cover:
1. Monthly budget (max rent per month) - ESSENTIAL. Always ask for their "monthly budget" explicitly.
2. Commute - ask in a simple, direct way like:
   "Where will you need to commute to? And how long are you willing to spend getting there?"
   Keep it short and conversational - don't try to ask about transport mode in the same question
3. Move-in date / timeline
4. How long they're looking to stay (minimum tenancy) - ask something like:
   "How long are you looking to stay? Some places require 6 or 12 month minimums."
5. Property preferences (house share vs flat, furnished, bills included)
6. Any deal-breakers (pets, couples, parking)

Current known preferences: {rules}

CONVERSATION FLOW:
- Ask ONE question at a time, naturally working through the topics above
- Be conversational - don't sound like a form or checklist
- Skip topics the user has already answered or that aren't relevant
- After 3-4 exchanges (or once the key points are covered), transition by saying something like:
  "Great, I think I have a good picture of what you're looking for! Take a look at the listings on the right - what do you think of them? Let me know if any catch your eye or if you'd like me to refine the search."

Be friendly and natural. The goal is to help, not interrogate."""


class Message(BaseModel):
    """A single message in a conversation."""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""
    message: str
    conversation_history: list[Message] = []


class ConversationRequest(BaseModel):
    """Request body for the find-matches endpoint."""
    conversation: list[Message]


# Filtering helpers
def _matches_yes(value: Any) -> bool:
    """Check if a value represents a 'yes' response."""
    if not value:
        return False
    return str(value).lower().strip() in ["yes", "y", "true", "1"]


def _matches_value(listing_val: Any, ideal_val: str) -> bool:
    """Check if a listing value contains the ideal value (case-insensitive)."""
    if not listing_val or not ideal_val:
        return True
    return ideal_val.lower() in str(listing_val).lower()


def filter_by_ideal(listings: list[dict[str, Any]], ideal: dict[str, Any]) -> list[dict[str, Any]]:
    """Filter listings based on ideal listing criteria."""
    filtered = listings

    if max_rent := ideal.get("max_rent"):
        filtered = [l for l in filtered if 0 < l["price"] <= max_rent]

    if min_rent := ideal.get("min_rent"):
        filtered = [l for l in filtered if l["price"] >= min_rent]

    if ideal.get("pets_ok") == "Yes":
        filtered = [l for l in filtered if _matches_yes(l.get("pets_ok"))]

    if ideal.get("couples_ok") == "Yes":
        filtered = [l for l in filtered if _matches_yes(l.get("couples_ok"))]

    if ideal.get("bills_included") == "Yes":
        filtered = [l for l in filtered if _matches_yes(l.get("bills_included"))]

    if ideal.get("parking") == "Yes":
        filtered = [l for l in filtered if _matches_yes(l.get("parking"))]

    if prop_type := ideal.get("property_type"):
        filtered = [l for l in filtered if _matches_value(l.get("property_type"), prop_type)]

    if furnishings := ideal.get("furnishings"):
        filtered = [l for l in filtered if _matches_value(l.get("furnishings"), furnishings)]

    return filtered


async def extract_rules_from_conversation(conversation: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Extract rules from the full conversation history."""
    all_user_text = " ".join(
        m["content"] for m in conversation if m["role"] == "user"
    )
    return await openai_client.extract_rules(all_user_text, [])


async def generate_response(
    message: str,
    conversation_history: list[dict[str, str]],
    rules: list[dict[str, Any]]
) -> str:
    """Generate assistant response based on conversation history and rules."""
    rules_text = ", ".join([f"{r['field']}: {r['value']}" for r in rules]) or "None yet"
    today = date.today().strftime("%A, %d %B %Y")
    system = SYSTEM_PROMPT.format(rules=rules_text, today=today)

    # Build messages for the API call
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]

    # Add conversation history (last 10 messages for context window management)
    for m in conversation_history[-10:]:
        messages.append({"role": m["role"], "content": m["content"]})

    # Add the current message
    messages.append({"role": "user", "content": message})

    return await openai_client.chat(messages)


@app.post("/api/chat")
async def chat(request: ChatRequest) -> dict[str, Any]:
    """Process a chat message and return assistant response with extracted rules.

    This endpoint is stateless - conversation history comes from the frontend.
    """
    # Convert Pydantic models to dicts
    conversation_history: list[dict[str, str]] = [
        {"role": m.role, "content": m.content} for m in request.conversation_history
    ]

    # Add new message to history for rule extraction
    full_conversation = conversation_history + [{"role": "user", "content": request.message}]

    # Extract rules from full conversation
    rules = await extract_rules_from_conversation(full_conversation)

    # Generate response
    assistant_message = await generate_response(request.message, conversation_history, rules)

    return {
        "assistantMessage": assistant_message,
        "hardRules": rules,
    }


@app.post("/api/find-matches")
async def find_matches(request: ConversationRequest) -> dict[str, Any]:
    """Full RAG pipeline: conversation -> ideal -> search -> filter -> rerank.

    This endpoint is stateless - receives full conversation from frontend.
    """
    conversation: list[dict[str, str]] = [
        {"role": m.role, "content": m.content} for m in request.conversation
    ]

    # 1. Generate ideal listing and summary in parallel
    ideal, summary = await asyncio.gather(
        openai_client.generate_ideal_listing(conversation),
        openai_client.summarize_conversation(conversation)
    )

    # 2. Vector search
    query_embedding = await openai_client.embed(summary)
    candidates = redis_client.search(query_embedding, top_k=50)

    # 3. Filter based on ideal listing
    filtered = filter_by_ideal(candidates, ideal)[:30]

    # 4. Rerank top candidates with GPT-4 + images in parallel
    async def score_one(listing: dict[str, Any]) -> dict[str, Any] | None:
        try:
            score = await openai_client.score_listing(
                conversation_summary=summary,
                ideal_listing=ideal,
                listing_summary=listing["summary"],
                image_urls=listing.get("image_urls", [])
            )
            return {
                "listing": listing,
                "score": score["overall_score"],
                "reasoning": score
            }
        except Exception as e:
            print(f"Scoring error: {e}")
            return None

    # Score all listings in parallel using asyncio.gather
    results = await asyncio.gather(*[score_one(listing) for listing in filtered[:15]])

    # Filter out None results (failed scoring) and sort by score
    scored = [r for r in results if r is not None]
    scored.sort(key=lambda x: x["score"], reverse=True)

    return {
        "idealListing": ideal,
        "summary": summary,
        "matches": scored
    }


@app.post("/api/find-matches-stream")
async def find_matches_stream(request: ConversationRequest):
    """Streaming RAG pipeline: returns results as they are scored."""
    conversation = [{"role": m.role, "content": m.content} for m in request.conversation]

    async def generate():
        # 1. Generate ideal listing and summary in parallel
        ideal, summary = await asyncio.gather(
            openai_client.generate_ideal_listing(conversation),
            openai_client.summarize_conversation(conversation)
        )

        # 2. Vector search
        query_embedding = await openai_client.embed(summary)
        candidates = redis_client.search(query_embedding, top_k=50)

        # 3. Filter based on ideal listing
        filtered = filter_by_ideal(candidates, ideal)[:30]
        to_score = filtered[:15]

        # Send initial data with candidates (unscored)
        yield f"data: {json.dumps({'type': 'init', 'total': len(to_score), 'idealListing': ideal, 'summary': summary})}\n\n"

        # 4. Score listings in parallel, yielding results as they complete
        async def score_one(listing: dict[str, Any], index: int) -> dict[str, Any] | None:
            try:
                score = await openai_client.score_listing(
                    conversation_summary=summary,
                    ideal_listing=ideal,
                    listing_summary=listing["summary"],
                    image_urls=listing.get("image_urls", [])
                )
                return {
                    "index": index,
                    "listing": listing,
                    "score": score["overall_score"],
                    "reasoning": score
                }
            except Exception as e:
                print(f"Scoring error: {e}")
                return None

        # Create tasks for all listings
        tasks = [asyncio.create_task(score_one(listing, i)) for i, listing in enumerate(to_score)]

        # Yield results as they complete
        for coro in asyncio.as_completed(tasks):
            result = await coro
            if result:
                yield f"data: {json.dumps({'type': 'score', 'match': result})}\n\n"

        # Send done signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
