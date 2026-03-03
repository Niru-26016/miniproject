import chromadb
import os

db_path = os.path.join(os.path.dirname(__file__), "brand_db")
client = chromadb.PersistentClient(path=db_path)

def peek_inside(brand_name=None):
    try:
        collection = client.get_collection(name="human_feedback")
        
        if brand_name:
            results = collection.get(where={"brand": brand_name.lower()})
        else:
            results = collection.get()

        print(f"\n---  Database Peek: {brand_name if brand_name else 'All Brands'} ---")
        print(f"Total Human Posts Found: {len(results['ids'])}")
        
        for i in range(min(3, len(results['ids']))):
            print(f"\n[{i+1}] Author: {results['metadatas'][i]['author']}")
            print(f"Content: {results['documents'][i][:150]}...")
            print("-" * 30)

    except Exception as e:
        print(f"Error: {e}. (Have you run /api/sync yet?)")

if __name__ == "__main__":
    peek_inside("Swiggy")