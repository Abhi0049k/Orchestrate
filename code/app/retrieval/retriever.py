import os
import time
import json
from pageindex import PageIndexClient

PI_API_KEY = os.environ.get("PAGEINDEX_API_KEY", "dummy_key")
pi_client = PageIndexClient(api_key=PI_API_KEY)

def get_doc_id_for_domain(domain: str) -> str:
    try:
        with open("doc_ids.json", "r") as f:
            mapping = json.load(f)
        return mapping.get(domain)
    except Exception:
        return None

def retrieve_from_pageindex(query: str, doc_id: str, top_k: int = 3):
    if not doc_id:
        return []
        
    try:
        response = pi_client.submit_query(doc_id=doc_id, query=query)
        retrieval_id = response.get("retrieval_id")
        if not retrieval_id:
            return []
            
        while True:
            retrieval = pi_client.get_retrieval(retrieval_id)
            status = retrieval.get("status")
            if status == "completed":
                break
            elif status == "failed":
                return []
            time.sleep(1)
        
        nodes = retrieval.get("retrieved_nodes", [])
        contexts = []
        for node in nodes[:top_k]:
            relevant_contents = node.get("relevant_contents", [])
            for group in relevant_contents:
                for item in group:
                    content = item.get("relevant_content")
                    if content:
                        # Format similar to what pipeline expects
                        contexts.append({"payload": {"text": content}})
        return contexts
    except Exception as e:
        print(f"Error retrieving from PageIndex: {e}")
        return []

def hybrid_search(query: str, domain_filter: str = None, top_k: int = 3):
    """
    Retrieves the most relevant chunks using PageIndex Vectorless RAG approach.
    """
    doc_id = get_doc_id_for_domain(domain_filter) if domain_filter else None
    
    if not doc_id:
        return []
    
    # Vectorless RAG using PageIndex
    contexts = retrieve_from_pageindex(query, doc_id, top_k=top_k)
    return contexts

if __name__ == "__main__":
    sample_query = "How do I reset my HackerRank password?"
    print(f"Testing vectorless search for: '{sample_query}'")
    results = hybrid_search(sample_query, domain_filter="hackerrank")
    for r in results:
        print(f"Text: {r['payload'].get('text')[:60]}...")
