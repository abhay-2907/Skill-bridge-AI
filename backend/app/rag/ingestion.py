"""
CareerPilot AI — Knowledge Base Document Ingestion
====================================================
What is this?
  Processes documents (text files, PDFs) into chunks, generates embeddings,
  and inserts them into the FAISS vector store.

Chunking strategy:
  We split text into overlapping chunks of ~512 tokens.
  Overlap of 50 tokens prevents important information from being split across
  chunk boundaries.

  Why overlap?
  If a sentence spans a chunk boundary, both chunks will contain part of it.
  Without overlap, that information might be missed during retrieval.
"""

import re
import logging
from pathlib import Path
from typing import Optional

from app.rag.retriever import faiss_retriever
from app.core.config import settings

logger = logging.getLogger(__name__)

# Approximate characters per token (rough estimate for splitting)
CHARS_PER_TOKEN = 4


class DocumentIngester:
    """
    Ingests documents into the FAISS vector store.

    Usage:
        ingester = DocumentIngester()
        ingester.ingest_text(
            text="Python is a programming language...",
            metadata={"title": "Python Guide", "document_type": "tutorial", "skill": "Python"}
        )
    """

    def __init__(self):
        self.chunk_size_chars = settings.CHUNK_SIZE * CHARS_PER_TOKEN
        self.overlap_chars = settings.CHUNK_OVERLAP * CHARS_PER_TOKEN

    def ingest_text(self, text: str, metadata: dict) -> int:
        """
        Chunk and ingest a text document.

        Returns: number of chunks created
        """
        if not text or len(text.strip()) < 50:
            logger.warning(f"Text too short to ingest: {metadata.get('title', 'Unknown')}")
            return 0

        chunks = self._chunk_text(text)
        if not chunks:
            return 0

        documents = [
            {"content": chunk, "metadata": metadata}
            for chunk in chunks
        ]

        faiss_retriever.add_chunks(documents)
        logger.info(f"Ingested {len(chunks)} chunks from '{metadata.get('title', 'Unknown')}'")
        return len(chunks)

    def _chunk_text(self, text: str) -> list[str]:
        """
        Split text into overlapping chunks.

        Strategy:
        1. Try to split at sentence boundaries ('. ', '? ', '! ')
        2. If a sentence is too long, split at word boundaries
        3. Add overlap between consecutive chunks
        """
        text = re.sub(r'\s+', ' ', text).strip()

        if len(text) <= self.chunk_size_chars:
            return [text]

        # Split into sentences first
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            if current_size + sentence_size > self.chunk_size_chars and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)

                # Keep last few sentences as overlap
                overlap_text = []
                overlap_size = 0
                for s in reversed(current_chunk):
                    if overlap_size + len(s) <= self.overlap_chars:
                        overlap_text.insert(0, s)
                        overlap_size += len(s)
                    else:
                        break

                current_chunk = overlap_text
                current_size = overlap_size

            current_chunk.append(sentence)
            current_size += sentence_size

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return [c for c in chunks if len(c.strip()) > 20]

    def ingest_knowledge_base_data(self, knowledge_base: list[dict]) -> int:
        """
        Ingest a list of structured knowledge base entries.

        Each entry should have:
        - text: the content
        - metadata: dict with title, document_type, role, skill, etc.
        """
        total_chunks = 0
        for entry in knowledge_base:
            text = entry.get("text", "")
            metadata = entry.get("metadata", {})
            if text:
                total_chunks += self.ingest_text(text, metadata)
        return total_chunks


document_ingester = DocumentIngester()
