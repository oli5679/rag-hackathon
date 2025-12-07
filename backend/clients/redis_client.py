import os
import json
import numpy as np
import redis
from redis.commands.search.field import VectorField, TextField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

EMBEDDING_DIM = 1536


class RedisClient:
    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=False
        )
        self.index_name = "idx_listings"

    def create_index(self):
        """Create vector search index for listings."""
        schema = (
            TextField("title"),
            TextField("summary"),
            TextField("location"),
            NumericField("price"),
            VectorField(
                "embedding",
                "HNSW",
                {"TYPE": "FLOAT32", "DIM": EMBEDDING_DIM, "DISTANCE_METRIC": "COSINE"}
            )
        )

        try:
            self.client.ft(self.index_name).dropindex(delete_documents=False)
        except:
            pass

        self.client.ft(self.index_name).create_index(
            schema,
            definition=IndexDefinition(prefix=["listing:"], index_type=IndexType.HASH)
        )

    def store_listing(self, listing: dict, embedding: list[float]) -> None:
        """Store a listing with its embedding."""
        key = f"listing:{listing['id']}"
        self.client.hset(key, mapping={
            "id": listing["id"],
            "title": listing["title"],
            "price": listing["price"],
            "location": listing["location"],
            "summary": listing["summary"],
            "imageUrl": listing.get("imageUrl", ""),
            "url": listing.get("url", ""),
            "data": json.dumps(listing),
            "embedding": np.array(embedding, dtype=np.float32).tobytes()
        })

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """Find top_k most similar listings by vector similarity."""
        query_bytes = np.array(query_embedding, dtype=np.float32).tobytes()

        query = Query(f"*=>[KNN {top_k} @embedding $vec AS score]").dialect(2)

        results = self.client.ft(self.index_name).search(
            query,
            query_params={"vec": query_bytes}
        )

        listings = []
        for doc in results.docs:
            listing = json.loads(doc.data)
            listing["score"] = float(doc.score)
            listings.append(listing)

        return sorted(listings, key=lambda x: x["score"])

    def ping(self) -> bool:
        """Check Redis connection."""
        try:
            return self.client.ping()
        except redis.ConnectionError:
            return False


redis_client = RedisClient()
