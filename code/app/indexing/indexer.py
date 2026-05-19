import os
import json
import time
from pathlib import Path
from pageindex import PageIndexClient

PI_API_KEY = os.environ.get("PAGEINDEX_API_KEY", "dummy_key")
pi_client = PageIndexClient(api_key=PI_API_KEY)

def index_corpus(data_dir: str):
    """Submits all markdown files to PageIndex and saves their doc_ids."""
    data_path = Path(data_dir)
    md_files = list(data_path.rglob("*.md"))
    
    print(f"Found {len(md_files)} markdown files in {data_dir}. Beginning indexing with PageIndex...")
    
    doc_ids_mapping = {}
    
    # Merge markdown files per domain
    domain_texts = {}
    for file_path in md_files:
        rel_path = file_path.relative_to(data_path)
        domain = rel_path.parts[0] if len(rel_path.parts) > 0 else "unknown"
        
        try:
            content = file_path.read_text(encoding="utf-8")
            if domain not in domain_texts:
                domain_texts[domain] = []
            domain_texts[domain].append(content)
        except Exception as e:
            print(f"Skipping {file_path} due to read error: {e}")
            
    for domain, texts in domain_texts.items():
        combined_text = "\n\n".join(texts)
        # Write to a temp file
        temp_file = data_path / f"{domain}_combined.md"
        temp_file.write_text(combined_text, encoding="utf-8")
        
        try:
            doc_info = pi_client.submit_document(str(temp_file))
            doc_id = doc_info["doc_id"]
            doc_ids_mapping[domain] = doc_id
            print(f"Submitted document for domain '{domain}', doc_id: {doc_id}")
            
            # Wait for it to be ready
            print(f"Waiting for document {doc_id} to be indexed...")
            max_retries = 30
            retry_count = 0
            while not pi_client.is_retrieval_ready(doc_id):
                if retry_count >= max_retries:
                    print("Timeout: Document processing took too long.")
                    break
                time.sleep(5)
                retry_count += 1
                
        except Exception as e:
            print(f"Error submitting to PageIndex: {e}")
            
        finally:
            if temp_file.exists():
                temp_file.unlink()
                
    # Save mapping to json
    with open("doc_ids.json", "w") as f:
        json.dump(doc_ids_mapping, f)
        
    print("Indexing complete.")

if __name__ == "__main__":
    index_corpus("../data")
