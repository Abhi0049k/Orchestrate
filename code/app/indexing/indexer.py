import os
from pathlib import Path
from retrieval.embeddings import get_embeddings_batch
from retrieval.vector_db_client import add_vectors, reset_db

def chunk_text(text: str, max_words=150, overlap_words=30) -> list[str]:
    """Splits text into smaller overlapping chunks for precise retrieval."""
    words = text.split()
    chunks = []
    if not words:
        return chunks
    
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + max_words])
        chunks.append(chunk)
        i += max_words - overlap_words
        
    return chunks

def index_corpus(data_dir: str):
    """Reads all markdown files from the data directory, chunks them, and indexes into FAISS."""
    print("Resetting FAISS index...")
    reset_db()
    
    data_path = Path(data_dir)
    md_files = list(data_path.rglob("*.md"))
    
    print(f"Found {len(md_files)} markdown files in {data_dir}. Beginning indexing...")
    
    vectors_batch = []
    payloads_batch = []
    batch_size = 50
    total_indexed = 0

    for file_path in md_files:
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Skipping {file_path} due to read error: {e}")
            continue
            
        # The first folder inside data/ determines the domain (e.g. claude, hackerrank, visa)
        rel_path = file_path.relative_to(data_path)
        domain = rel_path.parts[0] if len(rel_path.parts) > 0 else "unknown"
        
        chunks = chunk_text(content)
        for i, chunk in enumerate(chunks):
            # Contextualize the chunk for better embedding representation
            context_chunk = f"[{domain.upper()}] {chunk}"
            
            try:
                vec = get_embeddings_batch([context_chunk])[0]
            except Exception as e:
                print(f"Error generating embedding for chunk {i} of {file_path}: {e}")
                continue
                
            vectors_batch.append(vec)
            payloads_batch.append({
                "source": str(file_path),
                "domain": domain,
                "chunk_id": i,
                "text": chunk
            })
            
            if len(vectors_batch) >= batch_size:
                add_vectors(vectors_batch, payloads_batch)
                total_indexed += len(vectors_batch)
                print(f"Indexed {total_indexed} chunks...")
                vectors_batch = []
                payloads_batch = []
                
    # Index remaining
    if vectors_batch:
        add_vectors(vectors_batch, payloads_batch)
        total_indexed += len(vectors_batch)
        print(f"Indexed {total_indexed} chunks...")

    print("Indexing complete.")

if __name__ == "__main__":
    # Assumes the script is run from inside the `code` directory
    index_corpus("../data")
