from retrieval.embeddings import get_embedding
from retrieval.vector_db_client import search_vectors

def hybrid_search(query: str, domain_filter: str = None, top_k: int = 5):
    """
    Retrieves the most relevant chunks from the FAISS Vector DB using a hybrid approach.
    It first fetches a larger pool of semantically similar vectors (top_k * 3), 
    then filters/reranks based on the domain (if provided) and keywords.
    """
    # 1. Vector Search for initial semantic retrieval
    query_vec = get_embedding(query)
    
    # Retrieve a larger set to allow for filtering without missing out
    initial_k = top_k * 3 
    raw_results = search_vectors(query_vec, k=initial_k)
    
    # 2. Reranking and Filtering
    filtered_results = []
    query_keywords = set(query.lower().split())
    
    for res in raw_results:
        payload = res.get("payload", {})
        
        # Strict Domain Filtering: Skip if domain doesn't match
        if domain_filter and payload.get("domain") != domain_filter:
            continue
            
        # Optional Hybrid Reranking Logic: 
        # For this hackathon, we can apply a naive keyword match penalty.
        # If the chunk contains keywords from the query, we conceptually "boost" it
        # by artificially lowering its L2 distance (lower distance = more similar).
        chunk_text = payload.get("text", "").lower()
        chunk_keywords = set(chunk_text.split())
        
        overlap = query_keywords.intersection(chunk_keywords)
        bonus = len(overlap) * 0.05 # Adjust bonus weight as needed
        
        # In FAISS L2, lower distance is better, so we subtract the bonus
        adjusted_distance = res.get("distance", 0) - bonus
        res["distance"] = max(0, adjusted_distance) # prevent negative distance
        
        filtered_results.append(res)
        
    # Re-sort based on adjusted distance
    filtered_results.sort(key=lambda x: x["distance"])
    
    # Return the top K items
    return filtered_results[:top_k]

if __name__ == "__main__":
    # Simple test case when run standalone
    sample_query = "How do I reset my HackerRank password?"
    print(f"Testing hybrid search for: '{sample_query}'")
    results = hybrid_search(sample_query, domain_filter="hackerrank")
    for r in results:
        print(f"Distance: {r['distance']:.4f} | Source: {r['payload'].get('source')} | Text: {r['payload'].get('text')[:60]}...")
