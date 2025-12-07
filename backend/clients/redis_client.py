import os
import re
import json
from redisvl.index import SearchIndex
from redisvl.query import VectorQuery
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = f"redis://default:{os.getenv('REDIS_PASSWORD')}@{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}"
INDEX_NAME = "idx_flatshares_json"


class RedisClient:
    def __init__(self):
        self._index = None

    @property
    def index(self):
        if self._index is None:
            self._index = SearchIndex.from_existing(INDEX_NAME, redis_url=REDIS_URL)
        return self._index

    def search(self, query_embedding: list[float], top_k: int = 50) -> list[dict]:
        """Vector similarity search."""
        query = VectorQuery(
            vector=query_embedding,
            vector_field_name="json_vector",
            return_fields=["flatshare_id", "json_data", "images", "rent", "postcode"],
            num_results=top_k
        )
        results = self.index.query(query)
        return [self._parse_result(doc) for doc in results]

    def _parse_result(self, doc: dict) -> dict:
        """Parse Redis doc into listing dict."""
        data = json.loads(doc.get("json_data", "{}"))
        images = self._parse_images(doc.get("images", "[]"))

        return {
            "id": doc.get("flatshare_id"),
            "title": f"{data.get('room_type', 'Room')} in {data.get('location', 'London')}",
            "price": self._parse_rent(data.get("rent")),
            "location": data.get("location", ""),
            "postcode": data.get("postcode", ""),
            "imageUrl": images[0] if images else None,
            "image_urls": images,
            "summary": self._build_summary(data),
            "url": f"https://spareroom.co.uk/flatshare/flatshare_detail.pl?flatshare_id={doc.get('flatshare_id')}",
            "available": data.get("available"),
            "bills_included": data.get("bills_included"),
            "couples_ok": data.get("couples_ok"),
            "deposit": data.get("deposit"),
            "detail": data.get("detail"),
            "furnishings": data.get("furnishings"),
            "gender": data.get("gender"),
            "living_room": data.get("living_room"),
            "minimum_term": data.get("minimum_term"),
            "occupation": data.get("occupation"),
            "num_flatmates": data.get("num_flatmates"),
            "parking": data.get("parking"),
            "pets_ok": data.get("pets_ok"),
            "property_type": data.get("property_type"),
            "room_type": data.get("room_type"),
            "vector_distance": doc.get("vector_distance", 0),
        }

    def _parse_rent(self, rent_str) -> int:
        """Parse rent string to integer."""
        if not rent_str:
            return 0
        match = re.search(r'[\d,]+', str(rent_str).replace(',', ''))
        return int(float(match.group())) if match else 0

    def _parse_images(self, images_str: str) -> list[str]:
        """Parse images JSON to list of URLs."""
        if not images_str or images_str == "Unknown":
            return []
        try:
            images = json.loads(images_str)
            return images[:5] if isinstance(images, list) else []
        except (json.JSONDecodeError, TypeError):
            return []

    def _build_summary(self, data: dict) -> str:
        """Build a summary from listing data."""
        parts = []
        if data.get("room_type"):
            parts.append(data["room_type"])
        if data.get("location"):
            parts.append(f"in {data['location']}")
        if data.get("rent"):
            parts.append(f"- {data['rent']}")
        if data.get("detail"):
            detail = str(data["detail"])[:150]
            if len(str(data.get("detail", ""))) > 150:
                detail += "..."
            parts.append(f". {detail}")
        return " ".join(parts) if parts else "No description available"

    def ping(self) -> bool:
        """Check Redis connection."""
        try:
            return self.index is not None
        except Exception:
            return False


redis_client = RedisClient()
