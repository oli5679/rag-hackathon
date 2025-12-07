import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from data import LISTINGS
from clients import openai_client

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


class ScoreListingRequest(BaseModel):
    conversation_summary: str
    ideal_listing: dict
    listing_summary: str
    image_urls: list[str] = []


def filter_listings(rules: list) -> list:
    result = LISTINGS.copy()

    for rule in rules:
        field, value = rule.get("field"), rule.get("value")
        if field == "max_budget" and value:
            result = [l for l in result if l["price"] <= value]
        elif field == "location" and value:
            result = [l for l in result if value.lower() in l["location"].lower()]

    return result[:3]


def extract_rules(message: str, existing_rules: list) -> list:
    msg = message.lower()
    rules = list(existing_rules)

    if prices := re.findall(r'£(\d+)', message):
        rules = [r for r in rules if r.get("field") != "max_budget"]
        rules.append({"field": "max_budget", "value": int(prices[0]), "unit": "GBP"})

    locations = ["chelsea", "camden", "shoreditch", "brixton", "hampstead", "kensington", "zone 1", "central"]
    for loc in locations:
        if loc in msg:
            rules = [r for r in rules if r.get("field") != "location"]
            rules.append({"field": "location", "value": loc.title()})
            break

    if "pet" in msg:
        rules = [r for r in rules if r.get("field") != "pets_allowed"]
        rules.append({"field": "pets_allowed", "value": True})

    return rules


def generate_response(message: str, rules: list) -> str:
    rules_text = ", ".join([f"{r['field']}: {r['value']}" for r in rules]) or "None yet"
    system = SYSTEM_PROMPT.format(rules=rules_text)

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
        "topListings": filter_listings(current_rules)
    }


@app.get("/api/listings/top")
def get_top_listings(count: int = 3):
    return filter_listings(current_rules)[:count]


@app.get("/api/rules")
def get_rules():
    return {"hardRules": current_rules}


@app.put("/api/rules")
def update_rules(request: RulesRequest):
    global current_rules
    current_rules = request.hardRules
    return {"hardRules": current_rules, "topListings": filter_listings(current_rules)}


@app.post("/api/ideal-listing")
def get_ideal_listing(request: ConversationRequest):
    conversation = [{"role": m.role, "content": m.content} for m in request.conversation]
    return {"idealListing": openai_client.generate_ideal_listing(conversation)}


@app.post("/api/conversation-summary")
def get_conversation_summary(request: ConversationRequest):
    conversation = [{"role": m.role, "content": m.content} for m in request.conversation]
    return {"summary": openai_client.summarize_conversation(conversation)}


@app.post("/api/score-listing")
def score_listing(request: ScoreListingRequest):
    return openai_client.score_listing(
        conversation_summary=request.conversation_summary,
        ideal_listing=request.ideal_listing,
        listing_summary=request.listing_summary,
        image_urls=request.image_urls or None
    )


@app.get("/health")
def health():
    return {"status": "healthy"}
