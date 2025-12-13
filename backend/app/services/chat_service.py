from datetime import date
from typing import Dict, Any, List

# Note: We assume clients are available at the top level for now, 
# but eventually they might move to app/clients.
# For now we import from the root 'clients' package.
from clients import openai_client

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

async def extract_rules_from_conversation(conversation: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Extract rules from the full conversation history."""
    all_user_text = " ".join(
        m["content"] for m in conversation if m["role"] == "user"
    )
    return await openai_client.extract_rules(all_user_text, [])

async def generate_response(
    message: str,
    conversation_history: List[Dict[str, str]],
    rules: List[Dict[str, Any]]
) -> tuple[str, bool]:
    """Generate assistant response based on conversation history and rules."""
    rules_text = ", ".join([f"{r['field']}: {r['value']}" for r in rules]) or "None yet"
    today = date.today().strftime("%A, %d %B %Y")
    system = SYSTEM_PROMPT.format(rules=rules_text, today=today)

    # Build messages for the API call
    messages: List[Dict[str, str]] = [{"role": "system", "content": system}]

    # Add conversation history (last 10 messages for context window management)
    for m in conversation_history[-10:]:
        messages.append({"role": m["role"], "content": m["content"]})

    # Add the current message
    messages.append({"role": "user", "content": message})

    # Heuristic for suggesting search:
    # 1. We have at least 2 exchanges (4 messages including history)
    # 2. We have some rules extracted (at least budget is usually key)
    has_budget = any(r['field'] == 'max_budget' for r in rules)
    has_location = any(r['field'] in ['target_location', 'max_commute', 'location', 'postcode'] for r in rules)
    
    # Suggest search if we have budget + location OR decent conversation depth (> 2 exchanges) + some rules
    search_suggested = False
    if has_budget and has_location:
        search_suggested = True
    elif len(conversation_history) >= 4 and len(rules) > 0:
        search_suggested = True

    # If search is suggested, instruct the LLM to nudge the user
    if search_suggested:
        messages.append({
            "role": "system", 
            "content": "You have gathered enough information (budget, location, etc). Explicitly suggest that the user clicks the 'Find Matches' button now to see available properties."
        })

    response_text = await openai_client.chat(messages)

    return response_text, search_suggested
