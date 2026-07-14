# Candidate Compliance Agent 🗳️

An AI agent that lets anyone query Tamil Nadu 2026 candidate affidavits — assets, criminal records, income declarations — in plain English or Tamil.

🔗 **Live Demo:** https://affidavit-rag-frontend.vercel.app  
💻 **GitHub:** https://github.com/Haribabu05/candidate_rag

---

## The Problem

Every candidate contesting elections is legally required to submit affidavits declaring their assets, liabilities, criminal cases, and income. These documents are public — but effectively inaccessible.

They're scanned PDFs. In Tamil. Buried on government websites. Nobody reads them.

This project changes that.

---

## What It Does

- Ask about any candidate's assets, criminal record, income, or education
- Query in plain English or Tamil
- Get answers directly from official affidavit documents
- Follow-up questions suggested after every answer
- Remembers your past queries across sessions (Hindsight memory)

---

## Architecture

```
React Frontend (Vercel)
        ↓
    SESSION_ID
        ↓
Flask Backend (Railway)
        ↓
Hindsight Memory — Recall past context
        ↓
    Intent Router
        ↓
Structured Query  OR  Semantic RAG (ChromaDB)
        ↓
    Groq LLM (Llama 3.3 70B)
        ↓
Hindsight Memory — Retain new context
        ↓
Response + 4 Follow-up Questions
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vercel |
| Backend | Flask, Gunicorn, Railway |
| OCR | Tesseract (eng+tam, --psm 6) |
| Embeddings | paraphrase-multilingual-MiniLM-L12-v2 |
| Vector DB | ChromaDB |
| LLM | Groq API (Llama 3.3 70B Versatile) |
| Memory | Hindsight (Vectorize) |

---

## How It Works

### 1. OCR Pipeline

Scanned PDFs are converted to images at 300 DPI and OCR'd using Tesseract with Tamil + English language models:

```python
text = pytesseract.image_to_string(
    image,
    lang="eng+tam",
    config="--psm 6"
)
```

### 2. Semantic Chunking

Instead of naive 500-token page splits, each candidate gets 6 topic-specific documents:

- Identity & Contact
- Education
- Criminal Cases (structured)
- Criminal Detail (raw OCR)
- Income Tax
- Assets & Liabilities

35 candidates × 6 sections = **210 semantic documents** with precise retrieval.

### 3. Intent Router

Not every query needs RAG. The intent router handles:

| Intent | Handler |
|---|---|
| Party lookup | Direct structured query |
| Education filter | Direct structured query |
| Constituency search | Direct structured query |
| Candidate compare | Groq LLM with structured data |
| Summarize / Criminal / Affidavit | Semantic RAG |
| Unknown | Fuzzy candidate name matching |

### 4. Hindsight Memory

Every query recalls past context and stores new context:

```python
# Recall before answering
past_memory = recall_memory(session_id, query)

# Inject into prompt
prompt = f"Previous context: {past_memory}\n\nContext: {retrieved}\n\nQuestion: {query}"

# Store after answering
retain_memory(session_id, f"User asked: {query}. Answer: {answer}")
```

### 5. Follow-up Questions

After every answer, the LLM generates 4 contextual follow-up questions based on the query, retrieved context, and memory. These appear as clickable buttons.

---

## Project Structure

```
pdf_app/
├── backend/
│   ├── app.py                    # Flask API + chat endpoint
│   ├── semantic_search.py        # ChromaDB retrieval + RAG
│   ├── intent_router.py          # Query intent detection
│   ├── memory.py                 # Hindsight integration
│   ├── query_engine.py           # Structured queries + fuzzy search
│   ├── ingest.py                 # Semantic document builder
│   ├── extract_pipeline.py       # OCR pipeline
│   ├── ingest_pipeline.py        # Structured data extractor
│   ├── groq_client.py            # Groq LLM client
│   ├── answer_formatter.py       # Response formatting
│   ├── candidate_master_data.json
│   ├── extracted_pages.json
│   ├── chroma_db/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   └── App.css
│   └── package.json
└── data/
    └── KOLATHUR/                 # Source PDFs
```

---

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Tesseract OCR with Tamil language pack
- Poppler (for pdf2image)

### Backend

```bash
cd backend
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Add GROQ_API_KEY and HINDSIGHT_API_KEY

# Run OCR pipeline
python extract_pipeline.py

# Build structured data
python ingest_pipeline.py

# Build ChromaDB
python ingest.py

# Start server
python app.py
```

### Frontend

```bash
cd frontend
npm install
echo "REACT_APP_API_URL=http://localhost:5000" > .env
npm start
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/candidates` | List all candidates |
| GET | `/candidates/<name>` | Get candidate details |
| GET | `/party/<party>` | Candidates by party |
| GET | `/top-assets` | Top 10 by assets |
| POST | `/chat` | Main chat endpoint |

### Chat Request

```json
{
  "message": "Does MKStalin have any criminal cases?",
  "session_id": "abc123"
}
```

### Chat Response

```json
{
  "answer": "SSharan has no pending criminal cases.",
  "source": "semantic",
  "sources": [{"candidate": "SSharan", "section": "criminal_cases"}],
  "follow_ups": [
    "What are SSharan's total declared assets?",
    "What is SSharan's declared income?",
    "How does SSharan compare to other candidates?",
    "What is SSharan's educational qualification?"
  ]
}
```

---

## Data

- **35 candidates** from Kolathur constituency
- **619 pages** of OCR'd affidavit text
- **210 semantic documents** in ChromaDB
- **11 political parties** represented

---

## Deployment

**Backend → Railway**
1. Push to GitHub
2. Connect Railway to repo, set root directory to `backend`
3. Add `GROQ_API_KEY` and `HINDSIGHT_API_KEY` environment variables
4. Railway auto-detects Python and uses `Procfile`

**Frontend → Vercel**
1. Push frontend to GitHub
2. Connect Vercel, add `REACT_APP_API_URL` environment variable
3. Vercel auto-builds React

---

## Known Limitations

- 35 candidates only (scales to 4500+ with full OCR run)
- Structured data extraction has lower accuracy on Tamil tables due to OCR noise
- Railway.app domain may be blocked by some Indian ISPs

---

## Built With

- [Groq](https://groq.com) — Fast LLM inference
- [Hindsight by Vectorize](https://hindsight.vectorize.io) — Persistent agent memory
- [ChromaDB](https://www.trychroma.com) — Vector database
- [Sentence Transformers](https://www.sbert.net) — Multilingual embeddings
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) — Tamil + English OCR

---

## Author

**Haribabu S**  
[LinkedIn](https://linkedin.com/in/haribabu) · [GitHub](https://github.com/Haribabu05)

---

*Built during HackWithChennai 2.0*
