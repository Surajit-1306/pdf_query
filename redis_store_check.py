import redis
import numpy as np
from redis_setup import *

# Connect to Redis
# redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Check if the key exists
key = "pdf:cover_letter.pdf"
if redis_client.exists(key):
    stored_embedding = redis_client.get(key)
    embedding_array = np.frombuffer(stored_embedding, dtype=np.float32)
    print("Embedding stored:", embedding_array[:10])  # Print first 10 elements for verification
else:
    print("Key not found in Redis.")
