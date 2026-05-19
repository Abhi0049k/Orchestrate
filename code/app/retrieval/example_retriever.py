import csv
from pathlib import Path

class FewShotRetriever:
    def __init__(self, sample_csv_path: str):
        self.sample_csv_path = Path(sample_csv_path)
        self.metadata = []
        
    def build_index(self):
        """Reads sample tickets into memory."""
        if not self.sample_csv_path.exists():
            print(f"Sample CSV not found at {self.sample_csv_path}")
            return
            
        print("Loading few-shot examples...")
        with open(self.sample_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            examples = list(reader)
            
        for i, row in enumerate(examples):
            issue = row.get("Issue", "").strip()
            subject = row.get("Subject", "").strip()
            response = row.get("Response", "").strip()
            status = row.get("Status", "").strip()
            product_area = row.get("Product Area", "").strip()
            req_type = row.get("Request Type", "").strip()
            
            if not issue and not subject:
                continue
                
            text_to_match = f"{subject} {issue}".lower()
            
            self.metadata.append({
                "row_id": i,
                "issue": issue,
                "subject": subject,
                "response": response,
                "status": status,
                "product_area": product_area,
                "request_type": req_type,
                "text_to_match": text_to_match
            })
            
        print(f"Few-shot examples loaded: {len(self.metadata)}")
            
    def search_examples(self, query: str, product_area: str = None, top_k: int = 2) -> list:
        """Retrieves top-k relevant sample tickets using keyword overlap."""
        if not self.metadata:
            return []
            
        query_words = set(query.lower().split())
        
        results = []
        for meta in self.metadata:
            match_words = set(meta["text_to_match"].split())
            overlap = len(query_words.intersection(match_words))
            
            # Penalize examples that belong to a different known domain
            if product_area and product_area != "unknown":
                if meta.get("product_area") and meta.get("product_area").lower() != product_area.lower():
                    overlap -= 2
            
            # We want highest overlap first, so use negative overlap as distance
            results.append({
                "overlap": overlap,
                "metadata": meta
            })
            
        results.sort(key=lambda x: x["overlap"], reverse=True)
        return results[:top_k]

# Initialize the global retriever instance
few_shot_retriever = FewShotRetriever("../support_tickets/sample_support_tickets.csv")

