# CareerPilot AI — Comprehensive Documentation & Guide

> **Tagline:** Understand your skills. Find your gaps. Prepare smarter.

CareerPilot AI is an enterprise-grade, portfolio-ready career and interview preparation copilot designed for software engineers, students, and job seekers.

---

## 1. System Architecture

CareerPilot AI demonstrates how **Traditional Python/ML + NLP + RAG + Generative AI** operate synchronously:

```
Candidate Resume (PDF/DOCX)           Job Posting (Text/URL)
             │                                   │
             ▼                                   ▼
    [NLP Extractor / spaCy]             [NLP Job Classifier]
             │                                   │
             ▼                                   ▼
      Normalized Skills                   Required Skills
             └───────────────┬───────────────────┘
                             │
                             ▼
            [ML Skill Gap Engine (TF-IDF + Cosine)]
                             │
             ┌───────────────┴───────────────┐
             ▼                               ▼
     Exact & Partial Gaps            FAISS Vector Index
             │                               │
             └───────────────┬───────────────┘
                             │
                             ▼
              [RAG Context Construction]
                             │
                             ▼
                [IBM Granite / watsonx.ai]
                             │
             ┌───────────────┴───────────────┐
             ▼                               ▼
  Personalized Roadmap               Adaptive Mock Interview
```

---

## 2. Key Components & Educational Interview Guide

### Component A: Skill Normalization
- **What is it?** A dictionary-based canonicalizer mapping aliases (e.g. `ReactJS` $\to$ `React`, `Postgres` $\to$ `PostgreSQL`).
- **Why are we using it?** Prevents false negative mismatches where synonym variants prevent resume credit.
- **Interview Question:** *Why not use an LLM for normalization?*
  - **Answer:** LLMs introduce latency ($\sim 1\text{s}$ vs sub-millisecond dictionary lookups), cost, and stochastic variability. Rule-based normalization is deterministic and instantaneous.

### Component B: Skill Gap Engine (TF-IDF & Cosine Similarity)
- **What is it?** Set intersection for exact matches coupled with character n-gram TF-IDF vectorization to identify semantic relatives (e.g. `SQL` $\to$ `PostgreSQL`).
- **Why are we using it?** Accurately scores partial alignment without hallucinated scores.
- **Interview Question:** *What is Cosine Similarity?*
  - **Answer:** The cosine of the angle between two multi-dimensional vectors: $\frac{\mathbf{A} \cdot \mathbf{B}}{\|\mathbf{A}\|\|\mathbf{B}\|}$. A value of 1 signifies identical direction regardless of vector magnitude.

### Component C: Retrieval-Augmented Generation (RAG) with FAISS
- **What is it?** Ingests domain documentation into overlapping text chunks, vectorizes via `all-MiniLM-L6-v2`, stores them in FAISS, and fetches top-K relevant passages.
- **Why are we using it?** Grounds IBM Granite generation with verified source references, curbing hallucinations.
- **Interview Question:** *How does FAISS IndexFlatIP perform search?*
  - **Answer:** Computes exhaustive inner product (dot product) between the query vector and all indexed vectors. When vectors are unit-normalized ($L_2$), inner product is mathematically identical to cosine similarity.

---

## 3. Getting Started

### Local Development Setup

1. **Clone & Setup Environment:**
   ```bash
   cd careerpilot-ai
   cp .env.example backend/.env
   ```

2. **Run Backend:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python -m app.database.init_db
   python ../scripts/ingest_knowledge_base.py
   uvicorn app.main:app --reload --port 8000
   ```

3. **Run Frontend:**
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

4. **Run via Docker Compose:**
   ```bash
   docker-compose up --build
   ```

---

## 4. Technical Interview Questions to Master

1. **Q: Why decouple API schema (Pydantic) from Database models (SQLAlchemy)?**
   - **A:** Decoupling ensures internal database implementations (foreign keys, audit fields) are never unintentionally leaked over HTTP. It allows fine-grained request validation and versioning without altering relational tables.

2. **Q: How does CareerPilot AI handle prompt injection in uploaded resumes?**
   - **A:** User text is never directly interpolated as model instructions. Instead, documents are sandboxed inside isolated structural tags (`<resume_text>...</resume_text>`) with system prompts instructing the model to treat internal text strictly as inert candidate data.

3. **Q: What is the benefit of asynchronous database sessions in FastAPI?**
   - **A:** Python's `asyncio` event loop continues servicing incoming HTTP requests while waiting for PostgreSQL I/O responses, preventing thread blocking and scaling concurrency significantly under load.
