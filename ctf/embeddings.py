"""Embedding utilities for converting text to vectors for LanceDB."""

from transformers import AutoTokenizer, AutoModel
import torch


# Global cache for model and tokenizer
_embedding_model = None
_tokenizer = None


def get_embedding_model():
    """Lazy load embedding model."""
    global _embedding_model, _tokenizer
    if _embedding_model is None:
        # Use a lightweight embedding model
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
        _embedding_model = AutoModel.from_pretrained(model_name)
        _embedding_model.eval()
    return _embedding_model, _tokenizer


def embed_text(text: str) -> list[float]:
    """
    Convert text to embedding vector.

    Args:
        text: Text to embed

    Returns:
        List of floats representing the embedding vector
    """
    model, tokenizer = get_embedding_model()

    # Tokenize and encode
    inputs = tokenizer(
        text, return_tensors="pt", padding=True, truncation=True, max_length=512
    )

    # Generate embeddings
    with torch.no_grad():
        outputs = model(**inputs)
        # Use mean pooling to get sentence embedding
        embeddings = outputs.last_hidden_state.mean(dim=1).squeeze()

    # Convert to list of floats
    return embeddings.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Convert multiple texts to embedding vectors.

    Args:
        texts: List of texts to embed

    Returns:
        List of embedding vectors
    """
    model, tokenizer = get_embedding_model()

    # Tokenize and encode
    inputs = tokenizer(
        texts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512,
    )

    # Generate embeddings
    with torch.no_grad():
        outputs = model(**inputs)
        # Use mean pooling to get sentence embeddings
        embeddings = outputs.last_hidden_state.mean(dim=1)

    # Convert to list of lists of floats
    return embeddings.tolist()
