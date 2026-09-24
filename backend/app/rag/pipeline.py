"""
CareerPilot AI — RAG Pipeline Orchestrator
============================================
What is RAG?
  Retrieval-Augmented Generation combines:
  1. Retrieval: Find relevant documents from a knowledge base
  2. Generation: Pass those documents as context to an LLM

Why RAG instead of just asking the LLM?
  - LLMs have a knowledge cutoff and don't know your specific domain data
  - LLMs can hallucinate (confidently state wrong information)
  - RAG grounds the LLM's response in real, specific documents
  - RAG provides citations so users can verify answers

How this pipeline works:
  User Query
      ↓ embed query
  Query Vector
      ↓ FAISS search
  Top-K Relevant Chunks
      ↓ filter low-relevance chunks
  Context Construction
      ↓ inject into prompt
  IBM Granite
      ↓ generate grounded response
  Response + Citations

No-answer behavior:
  If no chunks meet the minimum relevance threshold, we do NOT let the LLM
  hallucinate. Instead we return a clear "not enough information" message.

Interview questions:
  Q: How do you prevent RAG from hallucinating?
  A: 1) Set a minimum similarity threshold — don't use low-relevance chunks
     2) Tell the LLM in the prompt to say "I don't know" if context is insufficient
     3) Return citations so users can check the source
     4) Use temperature=0 for more deterministic responses

  Q: What is chunking and why does it matter?
  A: Breaking documents into smaller pieces. Too large → irrelevant content
     dilutes the context. Too small → loses meaning. ~512 tokens with overlap
     is a common starting point.
"""

import logging
from typing import Optional

from app.rag.retriever import faiss_retriever
from app.ai.granite import ai_provider
from app.core.config import settings

logger = logging.getLogger(__name__)

# Minimum similarity score to include a chunk in context
MIN_RELEVANCE_SCORE = 0.25


class RAGPipeline:
    """
    Orchestrates the complete Retrieval-Augmented Generation pipeline.
    """

    def __init__(self):
        self.retriever = faiss_retriever
        self.ai = ai_provider

    async def query(
        self,
        user_query: str,
        prompt_template_fn,
        top_k: int = None,
        filters: Optional[dict] = None,
        **prompt_kwargs,
    ) -> dict:
        """
        Full RAG pipeline: retrieve → filter → construct context → generate.

        Args:
            user_query: The user's question
            prompt_template_fn: A function(rag_context, **kwargs) → prompt string
            top_k: Number of chunks to retrieve
            filters: Optional metadata filters for FAISS
            **prompt_kwargs: Additional kwargs passed to prompt_template_fn

        Returns:
            dict with: answer, sources, is_grounded, context_used
        """
        top_k = top_k or settings.TOP_K_RETRIEVAL

        # Step 1: Retrieve relevant chunks
        logger.info(f"RAG: Retrieving top-{top_k} chunks for query: '{user_query[:100]}'")
        chunks = self.retriever.search(user_query, top_k=top_k, filters=filters)

        # Step 2: Filter by minimum relevance threshold
        relevant_chunks = [c for c in chunks if c["score"] >= MIN_RELEVANCE_SCORE]
        logger.info(f"RAG: {len(relevant_chunks)}/{len(chunks)} chunks above threshold {MIN_RELEVANCE_SCORE}")

        # Step 3: Determine if we have sufficient grounding
        is_grounded = len(relevant_chunks) > 0

        if not is_grounded:
            logger.warning("RAG: No relevant chunks found. Returning no-answer response.")
            no_answer = (
                "I couldn't find enough relevant information in the current knowledge base "
                "to answer this confidently. Please try rephrasing, or this topic may not "
                "be covered in the current knowledge base."
            )
            return {
                "answer": no_answer,
                "sources": [],
                "is_grounded": False,
                "context_used": "",
            }

        # Step 4: Construct context from chunks
        context_parts = []
        for i, chunk in enumerate(relevant_chunks, 1):
            context_parts.append(
                f"[Source {i}: {chunk['title']}]\n{chunk['content']}"
            )
        rag_context = "\n\n---\n\n".join(context_parts)

        # Step 5: Build prompt with context injected
        prompt = prompt_template_fn(rag_context=rag_context, **prompt_kwargs)

        # Step 6: Generate response with IBM Granite
        logger.info("RAG: Sending prompt to AI provider...")
        answer = await self.ai.generate(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.3,
        )

        # Step 7: Build source citations
        sources = []
        for chunk in relevant_chunks:
            sources.append({
                "title": chunk.get("title", "Unknown"),
                "document_type": chunk.get("document_type", ""),
                "relevance_score": round(chunk["score"], 3),
                "content_preview": chunk["content"][:150] + "..." if len(chunk["content"]) > 150 else chunk["content"],
            })

        return {
            "answer": answer,
            "sources": sources,
            "is_grounded": True,
            "context_used": rag_context[:500] + "...",  # Truncated for logging
        }

    async def simple_generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> str:
        """
        Generate without RAG retrieval (for tasks that don't need context).
        Used for: roadmap generation, project recommendations, etc.
        """
        return await self.ai.generate(prompt=prompt, max_tokens=max_tokens, temperature=temperature)

    async def query_with_filter(
        self,
        user_query: str,
        prompt_fn,
        role: Optional[str] = None,
        document_type: Optional[str] = None,
        technology: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """
        RAG query with automatic metadata filtering.
        Example: role="backend", document_type="interview"
        """
        filters = {}
        if role:
            filters["role"] = role
        if document_type:
            filters["document_type"] = document_type
        if technology:
            filters["technology"] = technology

        return await self.query(
            user_query=user_query,
            prompt_template_fn=prompt_fn,
            filters=filters if filters else None,
            **kwargs,
        )


rag_pipeline = RAGPipeline()
