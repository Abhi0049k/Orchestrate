import json
import urllib.request
import urllib.error

FAISS_DB_URL = "http://localhost:8000"

def _make_request(endpoint: str, payload: dict = None):
    url = f"{FAISS_DB_URL}{endpoint}"
    data = json.dumps(payload).encode("utf-8") if payload else None
    
    # If data is provided, urllib defaults to POST
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'} if data else {})
    
    # If no data is provided, explicitly set method to POST
    if data is None:
        req.method = "POST"
        
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as e:
        error_body = e.read().decode("utf-8") if hasattr(e, 'read') else str(e)
        raise Exception(f"Request to {url} failed: {error_body}")

def add_vectors(vectors: list[list[float]], payloads: list[dict]):
    """Adds a batch of vectors and their corresponding payloads to the FAISS DB."""
    return _make_request("/add", {"vectors": vectors, "payloads": payloads})

def search_vectors(vector: list[float], k: int = 5):
    """Searches the FAISS DB for the most similar vectors."""
    res = _make_request("/search", {"vector": vector, "k": k})
    return res.get("results", [])

def reset_db():
    """Resets the FAISS Vector Database."""
    return _make_request("/reset")
