"""
CareerPilot AI — Curated Knowledge Base Ingestion Script
=========================================================
Ingests structured, high-quality interview preparation concepts,
role mappings, and technology guides into the FAISS vector index.
"""

import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.rag.ingestion import document_ingester

CURATED_KNOWLEDGE = [
    {
        "text": """
        Python Fundamentals for Backend Interviews:
        Python is an interpreted, high-level, dynamically typed language.
        Key concepts:
        - Memory management: Python uses reference counting and a cyclic garbage collector.
        - GIL (Global Interpreter Lock): A mutex that protects access to Python objects, preventing multiple threads from executing Python bytecodes at once. For CPU-bound tasks, use multiprocessing instead of threading.
        - Decorators: Higher-order functions that modify the behavior of another function without altering its source code.
        - Generators: Functions using 'yield' that return an iterator, evaluating items lazily to save memory.
        - Asyncio: Asynchronous I/O framework using an event loop, coroutines ('async def'), and 'await' for concurrency without OS threads.
        """,
        "metadata": {
            "title": "Python Backend Interview Core",
            "document_type": "interview_prep",
            "role": "Backend",
            "technology": "Python",
            "topic": "Language Internals",
            "difficulty": "intermediate"
        }
    },
    {
        "text": """
        Retrieval-Augmented Generation (RAG) Architecture:
        RAG optimizes LLM output by referencing an authoritative knowledge base outside of its training data before generating a response.
        Pipeline steps:
        1. Ingestion: Clean documents and split into chunks with small overlaps (e.g. 512 tokens with 50-token overlap).
        2. Vectorization: Convert text chunks into dense numeric embeddings using embedding models like all-MiniLM-L6-v2.
        3. Indexing: Store embeddings in a vector database like FAISS (Facebook AI Similarity Search).
        4. Retrieval: Vectorize user query and find top-K nearest neighbors using cosine similarity or inner product.
        5. Grounded Generation: Feed retrieved chunks alongside user prompt into an LLM (such as IBM Granite) to generate accurate answers with source citations.
        Benefits: Reduces hallucinations, keeps knowledge up-to-date without retraining, and provides verifiable citations.
        """,
        "metadata": {
            "title": "RAG Architecture and Implementation Guide",
            "document_type": "concept_guide",
            "role": "AI Engineer",
            "technology": "Generative AI",
            "topic": "RAG",
            "difficulty": "intermediate"
        }
    },
    {
        "text": """
        FastAPI Architecture and Best Practices:
        FastAPI is a modern, fast web framework for building APIs with Python 3.8+ based on standard Python type hints.
        Core advantages:
        - Asynchronous performance: Built on Starlette (for ASGI routing) and Pydantic (for data validation and serialization).
        - Dependency Injection system: 'Depends()' enables modular, testable auth, DB sessions, and security handlers.
        - Auto-generated documentation: Native interactive OpenAPI Swagger UI and ReDoc endpoints.
        - Background tasks: Simple background task dispatching for asynchronous jobs like email sending.
        """,
        "metadata": {
            "title": "FastAPI Web Framework Overview",
            "document_type": "concept_guide",
            "role": "Backend",
            "technology": "FastAPI",
            "topic": "API Design",
            "difficulty": "beginner"
        }
    },
    {
        "text": """
        Relational Database & SQL Optimization:
        PostgreSQL and SQL interview essentials:
        - Indexes: B-tree indexes speed up search queries (O(log n)) at the cost of slower INSERT/UPDATE writes. Composite indexes require matching column prefix order.
        - Transactions & ACID: Atomicity, Consistency, Isolation, Durability. Isolation levels (Read Uncommitted, Read Committed, Repeatable Read, Serializable) prevent anomalies like dirty reads, non-repeatable reads, and phantom reads.
        - Normalization: 1NF (atomic values), 2NF (no partial dependencies on composite keys), 3NF (no transitive dependencies).
        - Query Optimization: Use EXPLAIN ANALYZE to inspect query execution plans and detect sequential scans.
        """,
        "metadata": {
            "title": "SQL and Database Optimization Guide",
            "document_type": "interview_prep",
            "role": "Backend",
            "technology": "PostgreSQL",
            "topic": "Databases",
            "difficulty": "intermediate"
        }
    },
    {
        "text": """
        Docker and Containerization Fundamentals:
        Containers package application code together with dependencies, system tools, and libraries to ensure consistency across environments.
        - Image vs Container: An image is an immutable template; a container is a running instance of an image.
        - Dockerfile best practices: Multi-stage builds reduce final image size; order commands by change frequency to leverage layer caching; avoid running as root user.
        - Docker Compose: Multi-container orchestration tool defined via YAML to configure services, networks, and persistent volumes locally.
        """,
        "metadata": {
            "title": "Docker and DevOps Containerization Guide",
            "document_type": "concept_guide",
            "role": "DevOps",
            "technology": "Docker",
            "topic": "DevOps",
            "difficulty": "beginner"
        }
    }
]


def run_ingestion():
    print("Starting knowledge base ingestion into FAISS...")
    count = document_ingester.ingest_knowledge_base_data(CURATED_KNOWLEDGE)
    print(f"Successfully ingested {count} chunks into the vector store!")


if __name__ == "__main__":
    run_ingestion()
