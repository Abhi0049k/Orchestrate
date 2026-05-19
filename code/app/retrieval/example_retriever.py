import csv
import faiss
import numpy as np
from pathlib import Path
from retrieval.embeddings import get_embedding

class FewShotRetriever:
    def __init__(self, sample_csv_path: str):
        self.sample_csv_path = Path(sample_csv_path)
        self.index = None
        self.metadata = []
        
    def build_index(self):
        """Reads sample tickets, generates embeddings, and builds an in-memory FAISS index."""
        if not self.sample_csv_path.exists():
            print(f"Sample CSV not found at {self.sample_csv_path}")
            return
            
        print("Building few-shot examples FAISS index...")
        with open(self.sample_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            examples = list(reader)
            
        vectors = []
        for i, row in enumerate(examples):
            issue = row.get("Issue", "").strip()
            subject = row.get("Subject", "").strip()
            response = row.get("Response", "").strip()
            status = row.get("Status", "").strip()
            product_area = row.get("Product Area", "").strip()
            req_type = row.get("Request Type", "").strip()
            
            if not issue and not subject:
                continue
                
            # Preprocessing Heuristics: Prioritize Issue, down-weight/ignore noisy Subject
            noisy_keywords = ["help", "issue", "question", "support", "urgent", "error", "bug", "help needed"]
            is_noisy_subject = len(subject) < 8 or any(subject.lower() == k for k in noisy_keywords)
            
            if not issue:
                semantic_core = subject
            elif is_noisy_subject or not subject:
                semantic_core = issue
            else:
                # Append subject merely as secondary context
                semantic_core = f"{issue} (Context: {subject})"
                
            text_to_embed = f"{semantic_core}\nResponse: {response}\nStatus: {status}"
            try:
                vec = get_embedding(text_to_embed)
                vectors.append(vec)
                self.metadata.append({
                    "row_id": i,
                    "issue": issue,
                    "subject": subject,
                    "response": response,
                    "status": status,
                    "product_area": product_area,
                    "request_type": req_type,
                    "original_text": text_to_embed
                })
            except Exception as e:
                print(f"Failed to embed sample row {i}: {e}")
            
        if vectors:
            vec_array = np.array(vectors, dtype=np.float32)
            dim = vec_array.shape[1]
            self.index = faiss.IndexFlatL2(dim)
            self.index.add(vec_array)
            print(f"Few-shot index successfully built with {len(vectors)} examples.")
            
    def search_examples(self, query: str, product_area: str = None, top_k: int = 2) -> list:
        """Retrieves top-k relevant sample tickets using hybrid search logic."""
        if not self.index or self.index.ntotal == 0:
            return []
            
        try:
            query_vec = np.array([get_embedding(query)], dtype=np.float32)
        except Exception:
            return []
            
        initial_k = top_k * 3
        distances, indices = self.index.search(query_vec, min(initial_k, self.index.ntotal))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
                
            meta = self.metadata[idx]
            
            # Hybrid Semantic/Keyword Filtering:
            # Penalize examples that belong to a strictly different known domain
            if product_area and product_area != "unknown":
                if meta.get("product_area") and meta.get("product_area").lower() != product_area.lower():
                    dist += 0.5  # Artificial distance penalty to deprioritize cross-domain matches
            
            results.append({
                "distance": float(dist),
                "metadata": meta
            })
            
        # Re-sort by modified distance and return top K
        results.sort(key=lambda x: x["distance"])
        return results[:top_k]

# Initialize the global retriever instance
few_shot_retriever = FewShotRetriever("../support_tickets/sample_support_tickets.csv")
