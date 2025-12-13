"""SpareRoom Assistant API - FastAPI backend for room finding with RAG."""

from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
2. Commute - ask naturally in ONE question like:
   "Where do you commute to for work or study, how will you get there, and what's the max travel time you'd be happy with?"
   This captures: destination, transport mode, and acceptable time
3. Move-in date / timeline
4. Property preferences (house share vs flat, furnished, bills included)
5. Any deal-breakers (pets, couples, parking, minimum term)

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


class Rule(BaseModel):
    """A single search filter rule."""
    field: str
    value: str | int | bool
    unit: str | None = None


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""
    message: str
    conversation_history: list[Message] = []


class ChatResponse(BaseModel):
    """Response body for the chat endpoint."""
    assistantMessage: str
    hardRules: list[dict[str, Any]]


class ConversationRequest(BaseModel):
    """Request body for the find-matches endpoint."""
    conversation: list[Message]


class ScoredMatch(BaseModel):
    """A listing with its score and reasoning."""
    listing: dict[str, Any]
    score: int
    reasoning: dict[str, Any]


class MatchesResponse(BaseModel):
    """Response body for the find-matches endpoint."""
    idealListing: dict[str, Any]
    summary: str
    matches: list[ScoredMatch]


class HealthResponse(BaseModel):
    """Response body for the health endpoint."""
    status: str


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


def extract_rules_from_conversation(conversation: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Extract rules from the full conversation history."""
    # Combine all user messages to extract rules
    all_user_text = " ".join(
        m["content"] for m in conversation if m["role"] == "user"
    )
    return openai_client.extract_rules(all_user_text, [])


def generate_response(
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

    return openai_client.chat(messages)


@app.post("/api/chat", response_model=ChatResponse)
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
    rules = extract_rules_from_conversation(full_conversation)

    # Generate response
    assistant_message = generate_response(request.message, conversation_history, rules)

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

    # 1. Generate ideal listing and summary (can run in parallel)
    with ThreadPoolExecutor(max_workers=2) as executor:
        ideal_future = executor.submit(openai_client.generate_ideal_listing, conversation)
        summary_future = executor.submit(openai_client.summarize_conversation, conversation)
        ideal: dict[str, Any] = ideal_future.result()
        summary: str = summary_future.result()

    # 2. Vector search
    query_embedding = openai_client.embed(summary)
    candidates = redis_client.search(query_embedding, top_k=50)

    # 3. Filter based on ideal listing
    filtered = filter_by_ideal(candidates, ideal)[:30]

    # 4. Rerank top candidates with GPT-4 + images (parallel)
    def score_one(listing: dict[str, Any]) -> dict[str, Any]:
        score = openai_client.score_listing(
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

    scored: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(score_one, listing): listing for listing in filtered[:15]}
        for future in as_completed(futures):
            try:
                scored.append(future.result())
            except Exception as e:
                print(f"Scoring error: {e}")

    scored.sort(key=lambda x: x["score"], reverse=True)

    return {
        "idealListing": ideal,
        "summary": summary,
        "matches": scored
    }


@app.get("/health", response_model=HealthResponse)
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
