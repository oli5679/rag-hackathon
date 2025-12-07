from datetime import date
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from clients import openai_client
from clients.redis_client import redis_client

load_dotenv()

app = FastAPI(title="SpareRoom Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory state
current_rules: list[dict] = []
conversation_history: list[dict] = []

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


class ChatRequest(BaseModel):
    message: str


class RulesRequest(BaseModel):
    hardRules: list[dict]


class Message(BaseModel):
    role: str
    content: str


class ConversationRequest(BaseModel):
    conversation: list[Message]


# Filtering helpers
def _matches_yes(value) -> bool:
    if not value:
        return False
    return str(value).lower().strip() in ["yes", "y", "true", "1"]


def _matches_value(listing_val, ideal_val) -> bool:
    if not listing_val or not ideal_val:
        return True
    return ideal_val.lower() in str(listing_val).lower()


def filter_by_ideal(listings: list[dict], ideal: dict) -> list[dict]:
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


def rules_to_ideal(rules: list) -> dict:
    """Convert frontend rules to ideal listing format."""
    ideal = {}
    for rule in rules:
        field = rule.get("field")
        value = rule.get("value")

        if field == "max_budget":
            ideal["max_rent"] = value
        elif field == "location":
            ideal["location"] = value
        elif field == "pets_allowed":
            ideal["pets_ok"] = "Yes"
        elif field == "bills_included":
            ideal["bills_included"] = "Yes"

    return ideal


def get_listings_from_redis(rules: list) -> list[dict]:
    """Get listings from Redis with vector search and filtering."""
    # Build search query from rules
    ideal = rules_to_ideal(rules)
    query_parts = ["room to rent in London"]

    if location := ideal.get("location"):
        query_parts.append(f"in {location}")
    if ideal.get("max_rent"):
        query_parts.append(f"under £{ideal['max_rent']}")
    if ideal.get("pets_ok"):
        query_parts.append("pet friendly")

    query_text = " ".join(query_parts)
    query_embedding = openai_client.embed(query_text)

    # Vector search
    listings = redis_client.search(query_embedding, top_k=50)

    # Filter in Python
    filtered = filter_by_ideal(listings, ideal)

    return filtered[:3]


def extract_rules(message: str, existing_rules: list) -> list:
    """Extract hard rules using LLM for better natural language understanding."""
    return openai_client.extract_rules(message, existing_rules)


def generate_response(message: str, rules: list) -> str:
    rules_text = ", ".join([f"{r['field']}: {r['value']}" for r in rules]) or "None yet"
    today = date.today().strftime("%A, %d %B %Y")
    system = SYSTEM_PROMPT.format(rules=rules_text, today=today)

    conversation_history.append({"role": "user", "content": message})

    messages = [{"role": "system", "content": system}] + conversation_history[-10:]
    reply = openai_client.chat(messages)
    conversation_history.append({"role": "assistant", "content": reply})
    return reply


@app.post("/api/chat")
def chat(request: ChatRequest):
    global current_rules
    current_rules = extract_rules(request.message, current_rules)

    return {
        "assistantMessage": generate_response(request.message, current_rules),
        "hardRules": current_rules,
        "topListings": get_listings_from_redis(current_rules)
    }


@app.get("/api/rules")
def get_rules():
    return {"hardRules": current_rules}


@app.put("/api/rules")
def update_rules(request: RulesRequest):
    global current_rules
    current_rules = request.hardRules
    return {"hardRules": current_rules, "topListings": get_listings_from_redis(current_rules)}


@app.post("/api/find-matches")
def find_matches(request: ConversationRequest):
    """Full RAG pipeline: conversation → ideal → search → filter → rerank."""
    conversation = [{"role": m.role, "content": m.content} for m in request.conversation]

    # 1. Generate ideal listing and summary
    ideal = openai_client.generate_ideal_listing(conversation)
    summary = openai_client.summarize_conversation(conversation)

    # 2. Vector search
    query_embedding = openai_client.embed(summary)
    candidates = redis_client.search(query_embedding, top_k=50)

    # 3. Filter based on ideal listing
    filtered = filter_by_ideal(candidates, ideal)[:30]

    # 4. Rerank top candidates with GPT-4 + images
    scored = []
    for listing in filtered[:15]:
        score = openai_client.score_listing(
            conversation_summary=summary,
            ideal_listing=ideal,
            listing_summary=listing["summary"],
            image_urls=listing.get("image_urls", [])
        )
        scored.append({
            "listing": listing,
            "score": score["overall_score"],
            "reasoning": score
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    return {
        "idealListing": ideal,
        "summary": summary,
        "matches": scored
    }


@app.post("/api/reset")
def reset_state():
    """Reset all in-memory state (for page refresh)."""
    global current_rules, conversation_history
    current_rules = []
    conversation_history = []
    return {"status": "reset"}


@app.get("/health")
def health():
    return {"status": "healthy"}
