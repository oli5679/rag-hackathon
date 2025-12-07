import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
VISION_MODEL = "gpt-4o"


class OpenAIClient:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def embed(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=EMBEDDING_MODEL, input=text)
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
        return [item.embedding for item in response.data]

    def chat(self, messages: list[dict], max_tokens: int = 200) -> str:
        response = self.client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    def summarize_conversation(self, conversation: list[dict]) -> str:
        system = """Extract the information from the conversation in a structured format.
Focus on: what the user is looking for, their key requirements, preferences, and any deal-breakers.
Be concise and factual. Extract the data in the following format (JSON):

{"flatshare_id": None, 
"available": "string date or 'Now' or null",
 "bills_included": "Yes" or "No" or null,
  "couples_ok": "Yes" or "No" or null,
   "deposit": number (£ value) or null,
    "detail": free text description of ALL of the user's requirements and preferences for the flatshare, including any specific requirements for the room they are looking for. This should be a detailed description of the flatshare and the room they are looking for.
    "furnishings": "Furnished" or "Unfurnished" or null,
    "gender": "Males only" or "Females only" or null, 
    "living_room": "shared" or "private" or null, 
    "location": "string - preferred area/location", 
    "minimum_term": "string e.g. '6 months', '12 months' or null", 
    "occupation": "Professional" or "Student" or null, 
    "num_flatmates": number (integer) or null, 
    "parking": "Yes" or "No" or null, 
    "pets_ok": "Yes" or "No" or null, 
    "postcode": string postcode in the format or null, for example"SW17Area" (using the first identifier of the post code) + Area
    "property_type": "House share" or "Flat share" or "Studio" or null,
    "rent": number (£ value) or null, 
    "room_type": "single" or "double" or "triple" or "quad" or "queen" or "king" or "studio" or null
}
"""

        conv_text = "\n".join([f"{m['role']}: {m['content']}" for m in conversation])

        response = self.client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": conv_text}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content

    def generate_ideal_listing(self, conversation: list[dict]) -> dict:
        system = """Based on the conversation, create an ideal room listing that matches what the user is looking for.
Return JSON with this schema (use null for unspecified fields):
{
    "available": "string date or 'Now' or null",
    "bills_included": "Yes" or "No" or null,
    "couples_ok": "Yes" or "No" or null,
    "deposit": number or null,
    "detail": "string - detailed description of ideal room/property",
    "furnishings": "Furnished" or "Unfurnished" or null,
    "gender": "Males only" or "Females only" or null,
    "living_room": "shared" or "private" or null,
    "location": "string - preferred area/location",
    "minimum_term": "string e.g. '6 months', '12 months' or null",
    "occupation": "Professional" or "Student" or null,
    "parking": "Yes" or "No" or null,
    "pets_ok": "Yes" or "No" or null,
    "postcode": "string postcode area or null",
    "property_type": "House share" or "Flat share" or "Studio" or null,
    "max_rent": number - maximum monthly rent or null,
    "min_rent": number - minimum monthly rent or null
}
Extract preferences from the conversation. Only set fields that are mentioned or clearly implied."""

        conv_text = "\n".join([f"{m['role']}: {m['content']}" for m in conversation])

        response = self.client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": conv_text}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    def extract_rules(self, message: str, existing_rules: list[dict]) -> list[dict]:
        """Use LLM to extract hard requirements from a user message."""
        system = """You extract search filters from user messages about room hunting.

RULES:
- Only extract preferences, not vague mentions or questions
- Be reasonably strict: "under £700" or "max £700" → extract budget.
- "I need pets allowed" or "I have a dog" → extract pets_allowed. "do you allow pets?" → don't extract
- "in Camden" or "must be in zone 2" → extract location. "what's Camden like?" → don't extract
- If user states a preference confidently, extract it. If they're asking or unsure, don't.

Return a JSON array of rules. Each rule has: field, value, and optionally unit.
Supported fields:
- max_budget (integer, unit: "GBP")
- location (string - area name)
- pets_allowed (boolean)
- bills_included (boolean)
- couples_ok (boolean)
- parking (boolean)
- furnished (boolean)

Return the COMPLETE updated list (keep existing rules unless user contradicts them)."""

        rules_json = json.dumps(existing_rules) if existing_rules else "[]"

        response = self.client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Current rules: {rules_json}\n\nNew message: {message}"}
            ],
            response_format={"type": "json_object"},
            max_tokens=300
        )

        try:
            result = json.loads(response.choices[0].message.content)
            # Handle both {"rules": [...]} and direct [...] formats
            if isinstance(result, dict) and "rules" in result:
                return result["rules"]
            if isinstance(result, list):
                return result
            return existing_rules
        except (json.JSONDecodeError, KeyError):
            return existing_rules

    def score_listing(
        self,
        conversation_summary: str,
        ideal_listing: dict,
        listing_summary: str,
        image_urls: list[str] = None
    ) -> dict:
        system = """You are evaluating a room listing for a user searching for accommodation.

Analyze how well this listing matches the user's preferences and ideal listing criteria.

Return JSON with this schema:
{
    "location_match": {"reasoning": "string", "score": number (1-100)},
    "price_match": {"reasoning": "string", "score": number (1-100)},
    "amenities_match": {"reasoning": "string", "score": number (1-100)},
    "visual_quality": {"reasoning": "string", "score": number (1-100)},
    "overall_reasoning": "string - 2-3 sentence summary",
    "overall_score": number (1-100)
}

Be critical and realistic. 50 is average, 70+ is good, 90+ is excellent."""

        ideal_text = "\n".join([f"- {k}: {v}" for k, v in ideal_listing.items() if v is not None])

        user_content = [{
            "type": "text",
            "text": f"CONVERSATION SUMMARY:\n{conversation_summary}\n\nIDEAL LISTING CRITERIA:\n{ideal_text}\n\nLISTING TO EVALUATE:\n{listing_summary}"
        }]

        if image_urls:
            user_content.append({"type": "text", "text": "\nLISTING IMAGES:"})
            for url in image_urls[:5]:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": url, "detail": "low"}
                })

        response = self.client.chat.completions.create(
            model=VISION_MODEL if image_urls else CHAT_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            max_tokens=500
        )
        return json.loads(response.choices[0].message.content)


openai_client = OpenAIClient()
