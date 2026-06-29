---
title: Scholarship RAG
emoji: 🎓
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# 🎓 ScholarMatch AI

**An AI-powered scholarship discovery and recommendation platform for Indian students.**

ScholarMatch AI uses Retrieval-Augmented Generation (RAG) to match students with relevant government and private scholarship schemes based on their profile — caste category, state, income, and education level. An integrated AI chat advisor powered by Google Gemini answers student queries with cited, grounded responses.

---

## ✨ Features

- **Hybrid Search** — Combines dense semantic embeddings (`BAAI/bge-small-en-v1.5`) with sparse TF-IDF vectors in Qdrant for accurate retrieval.
- **AI Chat Advisor** — Gemini 2.5 Flash generates grounded answers, linking to specific scheme pages.
- **Personalised Recommendations** — Schemes are ranked by an eligibility scorer that weighs the user's category, state, income, and education level.
- **User Accounts** — JWT-based authentication with profile management.
- **Saved Schemes** — Bookmark favourite scholarships.
- **Dashboard** — Personalized dashboard with recommendations and statistics.
- **PDF Ingestion** — Automatically extracts scholarship information from government PDFs.
- **RAGAS Evaluation** — Evaluate retrieval and answer quality.

---

# 🗂️ Project Structure

```text
scholarship_Rag/
├── backend/
│   ├── auth/
│   ├── db/
│   ├── recommendation/
│   ├── routes/
│   ├── config.py
│   ├── schemas.py
│   └── main.py
├── frontend/
├── ingestion/
├── scraper/
├── data/
├── eval/
├── scripts/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# 🚀 Getting Started

## Prerequisites

- Python 3.11+
- Docker
- Node.js 20+

---

## Clone Repository

```bash
git clone https://github.com/aarushi2810/scholarship_Rag.git
cd scholarship_Rag
```

---

## Configure Environment

```bash
cp .env.example .env
```

Fill in:

- QDRANT_URL
- QDRANT_API_KEY
- POSTGRES_URL
- GEMINI_API_KEY
- JWT_SECRET
- REDIS_URL

---

## Install Backend

```bash
python -m venv .venv

source .venv/bin/activate
# Windows
# .venv\Scripts\activate

pip install -r requirements.txt
```

---

## Start Databases

```bash
docker compose up -d
```

This launches:

- PostgreSQL
- Redis
- Qdrant

---

## Index Scholarship Data

```bash
python -m ingestion.index_data
```

---

## Start Backend

```bash
uvicorn backend.main:app --reload --port 8000
```

Swagger UI:

```
http://localhost:8000/docs
```

---

## Start Frontend

```bash
cd frontend

npm install

npm run dev
```

---

# API

| Method | Endpoint |
|----------|-----------|
| POST | /auth/register |
| POST | /auth/login |
| GET | /profile |
| PUT | /profile |
| GET | /schemes |
| GET | /schemes/{id} |
| POST | /recommendations |
| POST | /chat |
| GET | /saved |
| POST | /saved/{scheme_id} |
| DELETE | /saved/{scheme_id} |
| GET | /dashboard |
| GET | /health |

---

# RAG Pipeline

```
User Query
      │
      ▼
Hybrid Search
(Dense + Sparse)
      │
      ▼
FlashRank Re-ranking
      │
      ▼
Gemini 2.5 Flash
      │
      ▼
Grounded Response
```

---

# PDF Ingestion

```bash
python -m scraper.pdf_parser data/raw/pdfs/
```

Extracts

- Eligibility
- Benefits
- Income Ceiling
- Deadline
- Categories
- Documents Required
- Education Levels

---

# Evaluation

```bash
python -m eval.<script_name>
```

Uses RAGAS metrics for retrieval quality.

---

# Docker

Build locally

```bash
docker build -t scholarship-rag .
```

Run

```bash
docker run -p 7860:7860 --env-file .env scholarship-rag
```

---

# Tech Stack

| Layer | Technology |
|--------|------------|
| Backend | FastAPI |
| Frontend | Next.js 16 |
| Database | PostgreSQL |
| Vector DB | Qdrant |
| Cache | Redis |
| Embeddings | BAAI/bge-small-en-v1.5 |
| Sparse Retrieval | TF-IDF |
| Re-ranking | FlashRank |
| LLM | Gemini 2.5 Flash |
| Authentication | JWT |
| Evaluation | RAGAS |

---

# Contributing

1. Fork repository

2. Create feature branch

```bash
git checkout -b feature/new-feature
```

3. Commit

```bash
git commit -m "Add feature"
```

4. Push

```bash
git push origin feature/new-feature
```

5. Open Pull Request

---

# License

MIT License.
