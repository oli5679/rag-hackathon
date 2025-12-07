import re
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

Your goal is to understand what the user is looking for by asking clarifying questions. Focus on gathering their preferences for:
- Budget (max/min rent)
- Location (area, postcode, transport links)
- Availability (move-in date)
- Property type (house share, flat share, studio)
- Room features (furnished, bills included, ensuite)
- Housemate preferences (professionals, students, gender)
- Lifestyle (pets, couples, parking, minimum term)

Current known preferences: {rules}

Be friendly and conversational. Ask ONE follow-up question at a time to clarify their requirements. Don't recommend specific listings yet - focus on understanding their needs."""


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
    """Extract hard rules only when user expresses a clear requirement.

    Only add rules when user uses strong language like 'must', 'need', 'max', 'under', 'require'.
    Casual mentions should stay in conversation, not become hard filters.
    """
    msg = message.lower()
    rules = list(existing_rules)

    # Only extract budget if it's clearly a max/limit (e.g., "max £700", "under £700", "budget is £700")
    budget_patterns = [
        r'(?:max|maximum|under|below|up to|budget[^£]*|no more than)\s*£(\d+)',
        r'£(\d+)\s*(?:max|maximum|or less|or under)',
    ]
    for pattern in budget_patterns:
        if match := re.search(pattern, msg):
            rules = [r for r in rules if r.get("field") != "max_budget"]
            rules.append({"field": "max_budget", "value": int(match.group(1)), "unit": "GBP"})
            break

    # Only extract location if user says "must be in", "need to be in", "only in", etc.
    locations = ["chelsea", "camden", "shoreditch", "brixton", "hampstead", "kensington", "zone 1", "central", "canary wharf", "greenwich", "stratford"]
    location_patterns = [r'(?:must be|need to be|only|has to be|require)[^.]*\b(' + '|'.join(locations) + r')\b']
    for pattern in location_patterns:
        if match := re.search(pattern, msg):
            rules = [r for r in rules if r.get("field") != "location"]
            rules.append({"field": "location", "value": match.group(1).title()})
            break

    # Only extract pet requirement if user says "must allow", "need to allow", "require"
    if re.search(r'(?:must|need|require|has to)[^.]*pet', msg):
        rules = [r for r in rules if r.get("field") != "pets_allowed"]
        rules.append({"field": "pets_allowed", "value": True})

    # Only extract bills if user explicitly requires it
    if re.search(r'(?:must|need|require)[^.]*bill[s]?\s+included', msg):
        rules = [r for r in rules if r.get("field") != "bills_included"]
        rules.append({"field": "bills_included", "value": True})

    return rules


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
    filtered = filter_by_ideal(candidates, ideal)[:10]

    # 4. Rerank top candidates with GPT-4 + images
    scored = []
    for listing in filtered[:5]:
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
