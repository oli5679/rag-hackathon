import os
import json
from dotenv import load_dotenv
from redisvl.index import SearchIndex
from redisvl.schema import IndexSchema
from redisvl.query import VectorQuery
from redisvl.utils.vectorize import OpenAITextVectorizer

# Load environment variables
load_dotenv()

def main():
    # 1. Setup Connection
    redis_host = "redis-12746.c74.us-east-1-4.ec2.cloud.redislabs.com"
    redis_port = "12746"
    redis_password = os.getenv("REDIS_PASSWORD")
    
    if not redis_password:
        print("Warning: REDIS_PASSWORD not found in environment variables.")
        return

    redis_url = f"redis://default:{redis_password}@{redis_host}:{redis_port}"

    # 2. Define/Load Schema
    # We need to provide the schema so RedisVL knows how to parse the fields back
    schema = IndexSchema.from_dict({
        "index": {
            "name": "idx_flatshares_json",
            "prefix": "doc",
            "storage_type": "hash",
        },
        "fields": [
            {"name": "flatshare_id", "type": "tag"},
            {"name": "postcode", "type": "text"},
            {"name": "rent", "type": "text"},
            {"name": "room_type", "type": "text"},
            {"name": "json_data", "type": "text"},
            {"name": "images", "type": "text"},
            {
                "name": "json_vector", 
                "type": "vector", 
                "attrs": {
                    "dims": 1536,
                    "algorithm": "hnsw",
                    "distance_metric": "cosine",
                    "datatype": "float32"
                }
            }
        ]
    })

    print(f"Connecting to Redis at {redis_host}...")
    index = SearchIndex(schema=schema)
    index.connect(redis_url)

    # 3. Initialize Vectorizer for the query
    print("Initializing OpenAI Vectorizer...")
    vectorizer = OpenAITextVectorizer(
        model="text-embedding-3-small"
    )

    # 4. Perform Query
    query_text = "Single or studio room in Bethnal Green"
    print(f"\nQuerying for: '{query_text}'")
    
    query_vec = vectorizer.embed(query_text)
    
    query = VectorQuery(
        vector=query_vec,
        vector_field_name="json_vector",
        return_fields=["flatshare_id", "rent", "json_data"],
        num_results=3
    )
    
    results = index.query(query)
    
    print(f"\nFound {len(results)} matches:\n")
    for i, doc in enumerate(results, 1):
        print(f"--- Result {i} ---")
        print(f"ID:   {doc['flatshare_id']}")
        print(f"Rent: {doc['rent']}")
        # Parse the JSON string back into a dict for nicer printing if desired
        try:
            data = json.loads(doc['json_data'])
            print(f"Detail snippet: {data.get('detail', '')[:150]}...")
        except:
            print("Could not parse json_data")
        print()

if __name__ == "__main__":
    main()