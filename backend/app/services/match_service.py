import asyncio
import json
from typing import Any, List, Dict, Optional, AsyncGenerator

from clients import openai_client
from clients.redis_client import redis_client

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


def filter_by_ideal(listings: List[Dict[str, Any]], ideal: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Filter listings based on ideal listing criteria."""
    filtered = listings

    # Rent filters
    if max_rent := ideal.get("max_rent"):
        filtered = [l for l in filtered if 0 < l.get("price", 0) <= max_rent]

    if min_rent := ideal.get("min_rent"):
        filtered = [l for l in filtered if l.get("price", 0) >= min_rent]

    # Boolean filters: strict "Yes" requirement
    boolean_fields = ["pets_ok", "couples_ok", "bills_included", "parking"]
    for field in boolean_fields:
        if ideal.get(field) == "Yes":
            filtered = [l for l in filtered if _matches_yes(l.get(field))]

    # String match filters: fuzzy contains check
    string_fields = ["property_type", "furnishings"]
    for field in string_fields:
        if value := ideal.get(field):
            filtered = [l for l in filtered if _matches_value(l.get(field), value)]

    return filtered


async def _prepare_candidates(conversation: List[Dict[str, str]]) -> tuple[Dict[str, Any], str, List[Dict[str, Any]]]:
    """Common pipeline steps 1-3: Generate Ideal -> Vector Search -> Filter."""
    # 1. Generate ideal listing and summary in parallel
    ideal, summary = await asyncio.gather(
        openai_client.generate_ideal_listing(conversation),
        openai_client.summarize_conversation(conversation)
    )

    # 2. Vector search
    query_embedding = await openai_client.embed(summary)
    candidates = redis_client.search(query_embedding, top_k=50)

    # 3. Filter based on ideal listing
    filtered = filter_by_ideal(candidates, ideal)
    
    return ideal, summary, filtered





async def stream_matches(conversation: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
    """Streaming RAG pipeline: returns results as they are scored."""
    
    # 1-3. Prepare candidates
    ideal, summary, to_score = await _prepare_candidates(conversation)

    # Send initial data with candidates (unscored)
    yield f"data: {json.dumps({'type': 'init', 'total': len(to_score), 'idealListing': ideal, 'summary': summary})}\n\n"

    # 4. Score listings in parallel, yielding results as they complete
    async def score_one(listing: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
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
