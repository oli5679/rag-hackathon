import pandas as pd
import numpy as np
import json
import os
from dotenv import load_dotenv
from redisvl.index import SearchIndex
from redisvl.schema import IndexSchema
from redisvl.utils.vectorize import OpenAITextVectorizer

# Load environment variables
load_dotenv()

def main():
    print("Loading data...")
    # Load the CSV
    df = pd.read_csv('listings.csv')

    # Define the columns to include (same as in convert_to_json.ipynb)
    columns = [
        'flatshare_id', 'available', 'bills_included', 'couples_ok', 'deposit', 
        'detail', 'furnishings', 'gender', 'living_room', 'location', 
        'minimum_term', 'occupation', 'num_flatmates', 'parking', 'pets_ok', 
        'postcode', 'property_type', 'rent', 'room_type'
    ]

    # Create new dataframe with selected columns
    new_df = df[columns].copy()

    # Fill NaNs to avoid JSON conversion issues or inconsistent data
    new_df = new_df.fillna("Unknown")


    
    # Replicating the logic from the notebook for json creation:
    print("Creating JSON data for embedding...")
    new_df['json_data'] = new_df.apply(lambda row: json.dumps(row.to_dict()), axis=1)
    new_df['images'] = df['images']

    # Define RedisVL Schema
    print("Defining schema...")
    schema = IndexSchema.from_dict({
        "index": {
            "name": "idx_flatshares_json",
            "prefix": "doc",
            "storage_type": "hash",
        },
        "fields": [
            # ID and Metadata fields
            {"name": "flatshare_id", "type": "tag"},
            {"name": "postcode", "type": "text"},
            {"name": "rent", "type": "text"},
            {"name": "room_type", "type": "text"},
            {"name": "json_data", "type": "text"},
            {"name": "images", "type": "text"},
            
            # The Vector Field
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

    # Initialize connection
    # Constructing Redis URL from env vars or hardcoded fallback based on notebook context
    redis_host = "redis-12746.c74.us-east-1-4.ec2.cloud.redislabs.com"
    redis_port = "12746"
    redis_password = os.getenv("REDIS_PASSWORD")
    
    if not redis_password:
        print("Warning: REDIS_PASSWORD not found in environment variables.")
    
    redis_url = f"redis://default:{redis_password}@{redis_host}:{redis_port}"

    print(f"Connecting to Redis at {redis_host}...")
    index = SearchIndex(schema=schema)
    index.connect(redis_url)

    # Create the index
    index.create(overwrite=True)

    # Initialize Vectorizer
    print("Initializing OpenAI Vectorizer...")
    vectorizer = OpenAITextVectorizer(
        model="text-embedding-3-small"
    )

    # Prepare data for insertion
    print("Vectorizing data (this may take a moment)...")
    records = new_df.to_dict(orient='records')
    
    # Extract the texts we want to embed (the json_data strings)
    texts_to_embed = [r['json_data'] for r in records]
    
    # Generate embeddings
    embeddings = vectorizer.embed_many(texts_to_embed)

    # Attach embeddings to records
    for i, record in enumerate(records):
        record['json_vector'] = np.array(embeddings[i], dtype=np.float32).tobytes()
        # Ensure ID is string for Redis
        record['flatshare_id'] = str(record['flatshare_id'])

    # Load into Redis
    print(f"Loading {len(records)} records into Redis...")
    index.load(records, id_field="flatshare_id")

    print("Done! Data indexed successfully.")
    
    # Simple test
    print("\nTesting search...")
    query_text = "ensuite double room in canary wharf"
    query_vec = vectorizer.embed(query_text)
    
    from redisvl.query import VectorQuery
    
    query = VectorQuery(
        vector=query_vec,
        vector_field_name="json_vector",
        return_fields=["flatshare_id", "rent", "json_data"],
        num_results=2
    )
    
    results = index.query(query)
    for doc in results:
        print(f"Match: ID {doc['flatshare_id']}, Rent: {doc['rent']}")

if __name__ == "__main__":
    main()


