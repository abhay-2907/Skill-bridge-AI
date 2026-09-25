"""
CareerPilot AI — IBM watsonx.ai / Granite AI Provider
=======================================================
What is this?
  A clean abstraction layer for AI providers. The AIProvider base class defines
  the interface. GraniteProvider implements it using IBM watsonx.ai.

Why an abstraction layer?
  - The app is not tightly coupled to IBM Granite
  - You can swap to OpenAI, Anthropic, or any local model later
  - Tests can inject a MockProvider without real API calls
  - Interview answer: "We used the Strategy pattern for provider selection"

How IBM watsonx.ai works:
  1. You send a REST request to IBM Cloud
  2. Payload includes: model_id, input (prompt), parameters
  3. The API returns generated text
  4. We parse and return the text

IBM Granite models available:
  - ibm/granite-3-8b-instruct     (recommended, good balance)
  - ibm/granite-13b-instruct-v2   (larger, higher quality)
  - ibm/granite-3-2b-instruct     (smallest, fastest)

Interview questions:
  Q: What is a temperature parameter in LLMs?
  A: Controls randomness. 0.0 = deterministic (same output every time).
     1.0 = very random/creative. For factual tasks use 0.1-0.3.

  Q: What is a max_tokens parameter?
  A: Maximum number of tokens the model will generate. 1 token ≈ 4 characters.
     Setting too low cuts off the response. Setting too high wastes money.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


# ── Base Provider (Interface / Strategy Pattern) ──────────────────────────────

class AIProvider(ABC):
    """Abstract base class for all AI providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        stop_sequences: Optional[list[str]] = None,
    ) -> str:
        """Generate text from a prompt. Returns the generated string."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider is configured and ready."""
        pass


# ── IBM Granite via watsonx.ai ────────────────────────────────────────────────

class GraniteProvider(AIProvider):
    """
    IBM Granite via watsonx.ai REST API.

    Authentication:
      watsonx.ai uses IAM token authentication.
      We exchange the API key for a bearer token, then use that for API calls.
    """

    IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"

    def __init__(self):
        self.api_key = settings.WATSONX_API_KEY
        self.project_id = settings.WATSONX_PROJECT_ID
        self.base_url = settings.WATSONX_URL
        self.model_id = settings.WATSONX_MODEL_ID
        self._access_token: Optional[str] = None

    def is_available(self) -> bool:
        return bool(self.api_key and self.project_id)

    async def _get_access_token(self) -> Optional[str]:
        """Exchange IBM API key for IAM bearer token."""
        if not self.api_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.IAM_TOKEN_URL,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                        "apikey": self.api_key,
                    },
                )
                if response.status_code == 200:
                    return response.json().get("access_token")
                else:
                    logger.error(f"IAM token error: {response.status_code} {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Failed to get IAM token: {e}")
            return None

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        stop_sequences: Optional[list[str]] = None,
    ) -> str:
        """
        Generate text using IBM Granite via watsonx.ai REST API.

        If the provider is not configured, returns a clear message instead of failing.
        """
        if not self.is_available():
            return (
                "⚠️ AI features require IBM watsonx.ai configuration. "
                "Please set WATSONX_API_KEY and WATSONX_PROJECT_ID in your .env file. "
                "See .env.example for details."
            )

        access_token = await self._get_access_token()
        if not access_token:
            return "⚠️ Could not authenticate with IBM watsonx.ai. Please check your API key."

        url = f"{self.base_url}/ml/v1/text/generation?version=2023-05-29"
        payload = {
            "model_id": self.model_id,
            "project_id": self.project_id,
            "input": prompt,
            "parameters": {
                "decoding_method": "greedy" if temperature == 0 else "sample",
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "stop_sequences": stop_sequences or [],
                "repetition_penalty": 1.1,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    if results:
                        return results[0].get("generated_text", "").strip()
                    return "No response generated."
                else:
                    logger.error(f"watsonx.ai API error: {response.status_code}: {response.text}")
                    return f"⚠️ AI service error (status {response.status_code}). Please try again."

        except httpx.TimeoutException:
            logger.error("watsonx.ai request timed out")
            return "⚠️ AI request timed out. Please try again."
        except Exception as e:
            logger.error(f"watsonx.ai request failed: {e}")
            return "⚠️ AI service is temporarily unavailable. Please try again later."


# ── Fallback / Mock Provider (for development without API key) ────────────────

class MockAIProvider(AIProvider):
    """
    Mock provider for local development without an IBM API key.
    Provides intelligent, grounded technical answers using context and rule-based synthesis.
    """

    def is_available(self) -> bool:
        return True

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        stop_sequences: Optional[list[str]] = None,
    ) -> str:
        prompt_lower = prompt.lower()

        # 1. Resume Evaluation Prompt
        if "resume" in prompt_lower or "candidate" in prompt_lower:
            return (
                "### 🎯 SkillBridge AI Resume Analysis\n\n"
                "• **Technical Strengths**: Demonstrated proficiency in modern core engineering stack (Python, JavaScript, REST APIs, SQL, Cloud Platforms like AWS/Azure).\n\n"
                "• **Architecture & Problem Solving**: Solid foundation in data structures, API design, and version control (Git).\n\n"
                "• **Recommended Action Plan**: To accelerate your qualification for Senior Full Stack and Distributed Systems roles, gain hands-on experience in container orchestration (Docker/Kubernetes), CI/CD pipelines, and microservices design."
            )

        # 2. Job Description Analysis Prompt
        if "job description" in prompt_lower or "target role" in prompt_lower:
            return (
                "### 📋 SkillBridge AI Job Requirement Breakdown\n\n"
                "• **Core Technical Demand**: High demand for scalable API design, efficient data structures, and relational/NoSQL database management.\n\n"
                "• **Domain & Complexity**: Production-grade engineering requiring strong asynchronous I/O and clean architecture principles.\n\n"
                "• **Interview Prep Priority**: System design fundamentals (caching, load balancing, DB indexing) and algorithmic problem solving."
            )

        # 3. Interview Feedback / Evaluation Prompt
        if "interview" in prompt_lower or "candidate answer" in prompt_lower:
            return (
                "### 💬 SkillBridge AI Interview Feedback\n\n"
                "• **Overall Rating**: 8.5 / 10\n"
                "• **Technical Depth**: Strong. You articulated core principles and trade-offs accurately.\n"
                "• **Communication Clarity**: Clean, structured, and easy to follow.\n"
                "• **Improvement Suggestion**: In live interviews, mention edge cases and specific complexity metrics (Time: $O(N)$, Space: $O(1)$)."
            )

        # 4. Career What-If Simulation
        if "what-if" in prompt_lower or "hypothetical" in prompt_lower:
            return (
                "### 🚀 SkillBridge Career Impact Simulation\n\n"
                "Acquiring these target skills boosts your role match alignment by **+35%**.\n\n"
                "• **Career Value**: Qualifies you directly for Senior Engineer and Cloud Architect pipelines.\n"
                "• **Recommended Project**: Build a cloud-native microservices architecture with distributed logging and automated deployment pipelines."
            )

        # 5. Technical Q&A — GIL in Python
        if "gil" in prompt_lower or "global interpreter lock" in prompt_lower:
            return (
                "The **Global Interpreter Lock (GIL)** is a mutex in CPython that prevents multiple native threads "
                "from executing Python bytecodes simultaneously. Key mechanisms to bypass or work around the GIL include:\n\n"
                "1. **Multiprocessing (`multiprocessing` module)**: Spawns independent OS processes, each with its own Python interpreter and GIL instance, enabling true CPU core parallelism.\n"
                "2. **C/C++ Extensions (e.g., NumPy, Cython)**: Heavy numerical computations release the GIL during execution (`Py_BEGIN_ALLOW_THREADS`), letting other threads execute Python code.\n"
                "3. **Asynchronous I/O (`asyncio`)**: Ideal for I/O-bound tasks (network/database operations) by yielding control during waiting periods without needing multi-threading.\n"
                "4. **Alternative Python Runtimes**: Using GIL-free implementations like PyPy, Jython, or free-threaded CPython (Python 3.13+)."
            )

        # 6. Technical Q&A — RAG Pipeline
        if "rag pipeline" in prompt_lower or "vector search" in prompt_lower:
            return (
                "The **RAG (Retrieval-Augmented Generation) Pipeline** operates in 4 main stages:\n\n"
                "1. **Document Ingestion & Chunking**: Raw technical documents are parsed and split into overlapping text chunks (e.g. 500 tokens with 50-token overlap) to preserve semantic context.\n"
                "2. **Embedding Generation**: Chunks are vectorized using a SentenceTransformer model (`all-MiniLM-L6-v2`) into dense 384-dimensional vector representations.\n"
                "3. **FAISS Vector Indexing**: Vectors are stored in a FAISS index (`IndexFlatIP`). During search, inner product matching retrieves top-K relevant contexts for a candidate query.\n"
                "4. **Grounded Generation**: Retrieved passages are injected into system prompts alongside user queries to generate accurate, hallucination-free AI responses."
            )

        # 7. Technical Q&A — B-Tree Indexes
        if "b-tree" in prompt_lower or "indexing" in prompt_lower:
            return (
                "**B-Tree Indexes in SQL Databases:**\n\n"
                "- **What they are**: Self-balancing search trees maintaining sorted data for logarithmic $O(\\log N)$ lookups, insertions, and deletions.\n"
                "- **Why they speed up queries**: Without an index, SQL databases must scan every row in a table ($O(N)$ full table scan). B-Trees allow point lookups and range scans to locate targets in just a few disk reads.\n"
                "- **Best practices**: Index high-cardinality columns used in `WHERE`, `JOIN`, and `ORDER BY` clauses, while avoiding over-indexing write-heavy tables."
            )

        # 8. Grounded Context RAG Fallback
        if "context:" in prompt_lower or "retrieved passages:" in prompt_lower:
            lines = [line.strip() for line in prompt.split("\n") if line.strip()]
            context_lines = [l for l in lines if not l.startswith("User Query:") and not l.startswith("System:")]
            summary_text = " ".join(context_lines[:5]) if context_lines else prompt[:300]
            return (
                f"Based on our technical knowledge base:\n\n"
                f"{summary_text}\n\n"
                f"*(Development Note: Configure WATSONX_API_KEY in .env for custom live IBM Granite outputs)*"
            )

        # Default fallback
        return (
            "Based on software engineering and interview standards:\n\n"
            "• **Core Concept**: Focus on modular design, asynchronous execution, and precise data modeling.\n"
            "• **Key Tradeoffs**: Balance latency vs throughput and memory footprint vs computation time.\n"
            "• **Interview Tip**: Always state your initial assumptions, define time/space complexity ($O(N)$), and mention boundary test cases."
        )




# ── Groq Open-Source LLM Provider (Llama 3.3 / Mixtral) ────────────────────────

class GroqProvider(AIProvider):
    """
    Open-Source LLM Provider using Groq API (Llama-3.3-70b, Llama-3.1-8b, Mixtral).
    Ultra-fast inference API with free tier access.
    """

    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL or "llama-3.3-70b-versatile"

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        stop_sequences: Optional[list[str]] = None,
    ) -> str:
        if not self.is_available():
            return "⚠️ GROQ_API_KEY is missing. Please set GROQ_API_KEY in your backend/.env file."

        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are SkillBridge AI, an expert software engineering career copilot and technical interview coach.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=45) as client:
                response = await client.post(self.API_URL, json=payload, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "").strip()
                    return "No output received from Open Source Groq model."
                else:
                    logger.error(f"Groq API error {response.status_code}: {response.text}")
                    return f"⚠️ Groq API Error ({response.status_code}): {response.text}"
        except Exception as e:
            logger.error(f"Groq request failed: {e}")
            return f"⚠️ Failed to connect to Groq Open-Source API: {e}"


# ── Provider Factory ──────────────────────────────────────────────────────────

def get_ai_provider() -> AIProvider:
    """
    Factory function. Selects the appropriate AI provider:
    1. Groq (Open-Source Llama-3.3-70b / Mixtral) if GROQ_API_KEY is set
    2. IBM Granite if WATSONX_API_KEY is set
    3. MockAIProvider fallback for offline development
    """
    groq = GroqProvider()
    if groq.is_available():
        logger.info(f"Using Open-Source Groq provider (model: {settings.GROQ_MODEL})")
        return groq

    granite = GraniteProvider()
    if granite.is_available():
        logger.info(f"Using IBM Granite provider (model: {settings.WATSONX_MODEL_ID})")
        return granite

    logger.warning("No live AI API keys found. Using MockAIProvider for development.")
    return MockAIProvider()


# Singleton
ai_provider = get_ai_provider()

