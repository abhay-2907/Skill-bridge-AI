"""
CareerPilot AI — RAG Embedding Service
=========================================
What is this?
  Converts text into dense vector representations (embeddings) using
  sentence-transformers. These vectors are stored in FAISS and used for
  semantic similarity search.

What is an embedding?
  A vector is a list of numbers. An embedding is a vector that captures the
  MEANING of text. Texts with similar meanings will have vectors that point
  in similar directions (high cosine similarity).

  Example:
  "Python programming language" → [0.12, -0.43, 0.87, ...]  (384 numbers)
  "Python coding" → [0.11, -0.41, 0.85, ...]  (similar direction)
  "Pizza recipe" → [-0.67, 0.23, -0.12, ...]  (very different direction)

Why sentence-transformers?
  - all-MiniLM-L6-v2 is small (80MB), fast, and produces good 384-dim embeddings
  - Runs locally — no API calls needed for embedding
  - Widely used in production RAG systems
  - License: Apache 2.0

Interview questions:
  Q: What is the difference between word2vec and sentence embeddings?
  A: word2vec gives one vector per word (ignores context).
     Sentence embeddings encode the entire sentence as one vector,
     capturing context and meaning more accurately.

  Q: What is dimensionality in embeddings?
  A: The length of the vector. all-MiniLM-L6-v2 produces 384-dimensional
     vectors. Larger dimensions = more expressive but more storage/compute.
"""

import logging
import numpy as np
from typing import Union

logger = logging.getLogger(__name__)

# Lazy load — only import when first used to save startup time
_model = None


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            from app.core.config import settings
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            _model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully.")
        except ImportError:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    return _model


class EmbeddingService:
    """
    Generates text embeddings using sentence-transformers.

    Usage:
        embedder = EmbeddingService()
        vector = embedder.embed("What is Python?")
        # → numpy array of shape (384,)

        vectors = embedder.embed_batch(["text1", "text2", "text3"])
        # → numpy array of shape (3, 384)
    """

    def embed(self, text: str) -> np.ndarray:
        """
        Embed a single text string.

        Args:
            text: The text to embed

        Returns:
            numpy array of shape (embedding_dim,)
        """
        if not text or not text.strip():
            from app.core.config import settings
            return np.zeros(settings.EMBEDDING_DIMENSION, dtype=np.float32)

        model = _get_model()
        vector = model.encode(
            text,
            normalize_embeddings=True,  # L2-normalize for cosine similarity
            show_progress_bar=False,
        )
        return vector.astype(np.float32)

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """
        Embed multiple texts efficiently in batches.

        Args:
            texts: List of text strings
            batch_size: Number of texts to encode at once

        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        if not texts:
            return np.array([])

        model = _get_model()
        vectors = model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 100,
        )
        return vectors.astype(np.float32)

    def cosine_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.
        Since vectors are L2-normalized, this is just the dot product.
        """
        return float(np.dot(vec_a, vec_b))


embedding_service = EmbeddingService()
