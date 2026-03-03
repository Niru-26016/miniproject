import chromadb
import os

db_path = os.path.join(os.path.dirname(__file__), "brand_db")
client = chromadb.PersistentClient(path=db_path)

def see_mappings():
    try:
        collection = client.get_collection(name="human_feedback")
        
        # 2. Get 1 sample with documents, metadatas, AND embeddings
        results = collection.get(
            limit=1,
            include=['embeddings', 'documents', 'metadatas']
        )

        if not results['ids']:
            print("Database is empty. Please run /api/sync/zomato after fixing main.py.")
            return

        print("\n=== CHROMADB INTERNAL MAPPING ===\n")
        
        # Mapping 1: The ID
        print(f"🔹 UNIQUE ID: {results['ids'][0]}")
        
        # Mapping 2: The Document (Human Text)
        print(f"🔹 DOCUMENT (The 'Human' Thought):")
        print(f"   \"{results['documents'][0][:100]}...\"")
        
        # Mapping 3: The Metadata (The Context)
        print(f"\n🔹 METADATA (The Logic Bridge):")
        print(f"   Brand: {results['metadatas'][0]['brand']}")
        print(f"   Author: {results['metadatas'][0]['author']}")
        
        # Mapping 4: The Embedding (The Vector)
        # These are the numbers the LLM uses to 'understand' meaning
        vector = results['embeddings'][0]
        print(f"\n🔹 EMBEDDING (Numerical Mapping):")
        print(f"   First 5 dimensions: {vector[:5]}...")
        print(f"   Total Vector Size: {len(vector)} numbers")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    see_mappings()