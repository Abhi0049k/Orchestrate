from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import faiss
import numpy as np

app = FastAPI()

# Global in-memory index and metadata storage
index = None
metadata = []

class VectorData(BaseModel):
    vectors: list[list[float]]
    payloads: list[dict] | None = None

class SearchQuery(BaseModel):
    vector: list[float]
    k: int = 5

@app.post("/add")
def add_vectors(data: VectorData):
    global index, metadata
    if not data.vectors:
        return {"status": "empty"}
    
    vecs = np.array(data.vectors, dtype=np.float32)
    dim = vecs.shape[1]
    
    # Initialize index on first insertion
    if index is None:
        index = faiss.IndexFlatL2(dim)
    
    if index.d != dim:
        raise HTTPException(status_code=400, detail=f"Dimension mismatch. Expected {index.d}, got {dim}")
        
    index.add(vecs)
    
    if data.payloads:
        metadata.extend(data.payloads)
    else:
        metadata.extend([{} for _ in range(len(vecs))])
        
    return {"status": "success", "total_vectors": index.ntotal}

@app.post("/search")
def search(query: SearchQuery):
    if index is None or index.ntotal == 0:
        return {"results": []}
        
    vec = np.array([query.vector], dtype=np.float32)
    if index.d != vec.shape[1]:
        raise HTTPException(status_code=400, detail=f"Dimension mismatch. Expected {index.d}, got {vec.shape[1]}")
        
    k = min(query.k, index.ntotal)
    distances, indices = index.search(vec, k)
    
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx != -1:
            results.append({
                "id": int(idx),
                "distance": float(dist),
                "payload": metadata[idx] if idx < len(metadata) else {}
            })
            
    return {"results": results}

@app.post("/reset")
def reset():
    global index, metadata
    index = None
    metadata = []
    return {"status": "reset_successful"}
