"""
CareerPilot AI — FAISS Vector Store & Retriever
=================================================
What is FAISS?
  Facebook AI Similarity Search (FAISS) is a library for efficient similarity
  search in high-dimensional vector spaces. It stores millions of vectors and
  finds the nearest neighbors in milliseconds.

How FAISS works internally:
  1. You add vectors to an index (IndexFlatL2 or IndexFlatIP)
  2. FAISS stores them in memory (or on disk as .faiss file)
  3. For a query vector, FAISS computes distance to ALL stored vectors
  4. Returns the K closest vectors (top-K nearest neighbors)

Index types used here:
  - IndexFlatIP: Inner Product (dot product) search → equivalent to cosine
    similarity when vectors are L2-normalized (which we do in embedder.py)

Why FAISS over other vector DBs?
  - Pure Python/C++ — no server to run
  - Excellent for local development and learning
  - Production scale: FAISS supports billions of vectors with IVF indexes
  - Open source (MIT license)

Metadata challenge:
  FAISS only stores vectors + integer IDs. It doesn't store metadata.
  We maintain a separate Python dict mapping FAISS index positions
  to metadata (chunk text, document title, source, etc.)

Interview questions:
  Q: What is approximate nearest neighbor (ANN) search?
  A: Finding vectors "close enough" to the query (not exactly closest).
     FAISS IVF indexes use ANN for speed. IndexFlat is exact but slower.

  Q: What is the difference between L2 and IP (inner product) distance?
  A: L2 = Euclidean distance (lower = more similar).
     IP = dot product (higher = more similar).
     For normalized vectors, cosine similarity == inner product.
"""

import os
import json
import pickle
import logging
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from app.rag.embedder import embedding_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class FAISSRetriever:
    """
    FAISS-based vector store for the RAG knowledge base.

    Stores:
    - FAISS index: the actual vectors (fast similarity search)
    - metadata store: dict mapping vector index → chunk metadata

    Persists to disk so you don't re-embed on every restart.
    """

    def __init__(self, index_path: Optional[str] = None):
        self.index_path = Path(index_path or settings.FAISS_INDEX_PATH)
        self.metadata_path = self.index_path.parent / "metadata.pkl"
        self.index: Optional[object] = None  # FAISS index
        self.metadata: list[dict] = []       # Parallel list to FAISS vectors
        self._load_or_create()

    def _load_or_create(self):
        """Load existing FAISS index from disk, or create a new empty one."""
        if not FAISS_AVAILABLE:
            logger.warning("faiss-cpu not installed. RAG retrieval will be disabled.")
            return

        if self.index_path.with_suffix(".faiss").exists() and self.metadata_path.exists():
            try:
                self.index = faiss.read_index(str(self.index_path.with_suffix(".faiss")))
                with open(self.metadata_path, "rb") as f:
                    self.metadata = pickle.load(f)
                logger.info(f"FAISS index loaded: {self.index.ntotal} vectors")
            except Exception as e:
                logger.error(f"Failed to load FAISS index: {e}. Creating new index.")
                self._create_new_index()
        else:
            self._create_new_index()

    def _create_new_index(self):
        """Create a new empty FAISS index."""
        if not FAISS_AVAILABLE:
            return
        dim = settings.EMBEDDING_DIMENSION
        # IndexFlatIP: exact inner product search (cosine similarity for normalized vectors)
        self.index = faiss.IndexFlatIP(dim)
        self.metadata = []
        logger.info(f"Created new FAISS index (dim={dim})")

    def add_chunks(self, chunks: list[dict]):
        """
        Add text chunks to the FAISS index.

        Args:
            chunks: List of dicts with keys:
                - content (str): The text to embed
                - metadata (dict): title, source, document_type, role, etc.

        How it works:
        1. Extract text from each chunk
        2. Generate embeddings in batch (efficient)
        3. Add vectors to FAISS index
        4. Store metadata in parallel list
        5. Save to disk
        """
        if not FAISS_AVAILABLE or not chunks:
            return

        texts = [chunk["content"] for chunk in chunks]
        logger.info(f"Embedding {len(texts)} chunks...")

        # Batch embed all chunks
        vectors = embedding_service.embed_batch(texts)

        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        # Add to FAISS
        self.index.add(vectors)

        # Store metadata (parallel to vectors)
        for chunk in chunks:
            self.metadata.append({
                "content": chunk["content"],
                "title": chunk.get("metadata", {}).get("title", "Unknown"),
                "source": chunk.get("metadata", {}).get("source", ""),
                "document_type": chunk.get("metadata", {}).get("document_type", ""),
                "role": chunk.get("metadata", {}).get("role", ""),
                "technology": chunk.get("metadata", {}).get("technology", ""),
                "skill": chunk.get("metadata", {}).get("skill", ""),
                "topic": chunk.get("metadata", {}).get("topic", ""),
                "difficulty": chunk.get("metadata", {}).get("difficulty", ""),
            })

        self._save()
        logger.info(f"FAISS index now has {self.index.ntotal} vectors")

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[dict] = None,
    ) -> list[dict]:
        """
        Search for the most relevant chunks for a query.

        Pipeline:
        1. Embed the query text
        2. Search FAISS for top-K nearest vectors
        3. Apply optional metadata filters
        4. Return ranked results with scores

        Args:
            query: The user's question or search text
            top_k: Number of results to return
            filters: Optional dict of metadata fields to filter by
                     e.g. {"document_type": "interview", "role": "backend"}

        Returns:
            List of dicts with: content, score, title, source, metadata
        """
        if not FAISS_AVAILABLE or self.index is None:
            logger.warning("FAISS not available. Returning empty results.")
            return []

        if self.index.ntotal == 0:
            logger.warning("FAISS index is empty. Please ingest knowledge base first.")
            return []

        # Embed query
        query_vector = embedding_service.embed(query)
        query_vector = query_vector.reshape(1, -1)

        # Search — fetch more than top_k to allow for filtering
        fetch_k = min(top_k * 3, self.index.ntotal)
        scores, indices = self.index.search(query_vector, fetch_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue  # FAISS returns -1 for invalid results

            meta = self.metadata[idx]

            # Apply metadata filters
            if filters:
                skip = False
                for filter_key, filter_value in filters.items():
                    if meta.get(filter_key, "").lower() != filter_value.lower():
                        skip = True
                        break
                if skip:
                    continue

            results.append({
                "content": meta["content"],
                "score": float(score),
                "title": meta.get("title", "Unknown"),
                "source": meta.get("source", ""),
                "document_type": meta.get("document_type", ""),
                "role": meta.get("role", ""),
                "technology": meta.get("technology", ""),
                "topic": meta.get("topic", ""),
                "difficulty": meta.get("difficulty", ""),
            })

            if len(results) >= top_k:
                break

        return results

    def _save(self):
        """Save the FAISS index and metadata to disk."""
        if not FAISS_AVAILABLE or self.index is None:
            return
        try:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.index, str(self.index_path.with_suffix(".faiss")))
            with open(self.metadata_path, "wb") as f:
                pickle.dump(self.metadata, f)
            logger.info("FAISS index saved to disk.")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")

    def get_stats(self) -> dict:
        """Return statistics about the vector store."""
        return {
            "total_vectors": self.index.ntotal if (FAISS_AVAILABLE and self.index) else 0,
            "index_path": str(self.index_path),
            "faiss_available": FAISS_AVAILABLE,
            "metadata_count": len(self.metadata),
        }

    def clear(self):
        """Clear the index (use carefully!)."""
        self._create_new_index()
        self._save()
        logger.warning("FAISS index cleared!")


# Singleton — shared across the application
faiss_retriever = FAISSRetriever()
