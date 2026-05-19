from langchain_ollama import OllamaEmbeddings

# Initialize the Langchain Ollama Embeddings model
# This connects to the local Ollama instance running at localhost:11434 by default
embeddings_model = OllamaEmbeddings(model="nomic-embed-text:latest")

def get_embedding(text: str) -> list[float]:
    """Generates a single embedding using Langchain's Ollama integration."""
    return embeddings_model.embed_query(text)

def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generates embeddings for a batch of texts using Langchain."""
    return embeddings_model.embed_documents(texts)
