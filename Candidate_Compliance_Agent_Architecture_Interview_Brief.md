# Candidate Compliance Agent — AI Interview Brief

## Instructions for the interviewer AI

Interview the candidate about this project as if assessing an entry-level AI/ML or full-stack engineer. Begin with the 60-second project explanation, then progressively ask questions about architecture, RAG, OCR, embeddings, ChromaDB, Flask routing, frontend-backend communication, Hindsight memory, limitations, and improvements. Ask one question at a time. After each response, give short, concrete feedback: what was accurate, what was missing, and how to say it better. Challenge vague claims and ask follow-up questions.

The candidate should be evaluated for clear understanding rather than memorized wording. Expect them to distinguish implemented behavior from planned improvements.

## 1. Project overview

Candidate Compliance Agent is a bilingual, conversational application for exploring Tamil Nadu election-candidate affidavits. It makes disclosures such as assets, liabilities, income, education, and criminal-case information easier to search.

The source information is public, but hard to use because affidavits are scanned PDFs, often contain Tamil and English, and include dense tables. The application converts the affidavits into searchable data and lets a user ask natural-language questions.

Current dataset scope:

- 35 candidates from the Kolathur constituency.
- Hundreds of OCR-extracted affidavit pages.
- Structured candidate records plus semantic affidavit documents in ChromaDB.

## 2. One-minute explanation

"Candidate Compliance Agent is a hybrid RAG application that makes public election affidavits easier to understand. I ingest scanned candidate-affidavit PDFs, convert them to images, run Tamil and English OCR, and use the extracted text in two ways. First, I parse predictable fields into structured candidate data for exact tasks such as party, education, constituency, gender, and comparison queries. Second, I store semantically meaningful affidavit sections in ChromaDB so that open-ended questions—such as criminal disclosures or asset explanations—can use retrieval-augmented generation. The React frontend sends each question and a session ID to a Flask backend. Flask recalls relevant conversation memory from Hindsight, detects the user’s intent, routes internally to structured search or semantic RAG, and returns an answer, sources, and suggested follow-up questions. The LLM is Groq-hosted Llama 3.3 70B, and it is prompted to answer only from retrieved affidavit context for RAG questions." 

## 3. System architecture

### Online request flow

```text
React frontend
  └─ sendMessage()
       └─ POST /chat { message, session_id }
            └─ Flask chat() endpoint
                 ├─ recall Hindsight memory
                 ├─ detect intent
                 ├─ structured handler OR semantic RAG OR fallback
                 ├─ generate answer and follow-ups
                 ├─ retain useful memory summary
                 └─ return JSON to React
React renders answer, sources, and clickable follow-ups.
```

### Offline ingestion flow

```text
Official scanned affidavit PDFs
  └─ PDF pages converted to 300-DPI images
       └─ Tesseract OCR with Tamil + English
            └─ page text plus candidate/page/party metadata
                 ├─ affidavit parser → candidate_master_data.json
                 └─ semantic documents → embeddings → ChromaDB
```

## 4. Frontend: React

The frontend lives in `frontend/src/App.js`.

### `sendMessage()`

This is the function invoked when the user clicks the send button or presses Enter. It:

1. Adds the user message to the local chat state.
2. Sends a `POST` request to `${API}/chat`.
3. Includes the current message and `SESSION_ID` in JSON.
4. Receives `answer`, `source`, `sources`, and `follow_ups`.
5. Adds the assistant response to the local message state so the UI renders it.

Example request:

```json
{
  "message": "Explain MKStalin's criminal disclosure",
  "session_id": "k8p3zq1m"
}
```

### Session ID behavior

The current frontend creates the ID when the React module loads:

```javascript
const SESSION_ID = Math.random().toString(36).substring(2, 10);
```

The same ID is sent for all messages while that page instance is open. It is not saved to `sessionStorage`, local storage, or a cookie. Therefore, refreshing, reopening the site, or opening a new tab creates a new ID. This is session-scoped conversational context, not authenticated account-level memory.

### Follow-up suggestions

React only displays suggestions; it does not generate them. It maps `data.follow_ups` into buttons. Clicking a button calls `setMessage(q)`, which fills the input box. The user then sends that text using the usual `sendMessage()` flow.

## 5. Flask backend and routes

The Flask backend is in `backend/app.py`.

### Main conversational endpoint

| Method | URL | Purpose |
| --- | --- | --- |
| POST | `/chat` | Main agent endpoint. It recalls memory, detects intent, calls an internal handler, retains memory, and returns the answer. |

Important: the intent router does **not** redirect the user to different Flask URLs. React always calls `/chat`. Flask makes internal Python function calls based on the detected intent.

### Direct REST endpoints

| Method | URL | Purpose |
| --- | --- | --- |
| GET | `/` | Health check. |
| GET | `/candidates` | List all candidate names. |
| GET | `/candidates/<name>` | Return the full structured record for an exact candidate name. |
| GET | `/party/<party>` | Return candidate names for a party. |
| GET | `/region/<region>` | Return candidate names for a constituency/region. |
| GET | `/compare?c1=<name>&c2=<name>` | Return raw structured records for two candidates. |
| GET | `/education/<degree>` | Return candidate names with an exact degree match. |
| GET | `/top-assets` | Return the top ten candidates by declared total assets. |

These direct REST URLs are available for direct clients. The existing chat UI uses `/chat`, not these URLs.

## 6. The `/chat` request lifecycle

1. Flask reads `message` and `session_id` from JSON.
2. Flask calls `recall_memory(session_id, query)` before deciding the handler.
3. Flask calls `detect_intent(query)`.
4. Flask calls the appropriate internal handler.
5. Flask creates an answer; some paths also create follow-up questions.
6. Flask calls `retain_memory()` with a concise interaction summary.
7. Flask returns a JSON payload for React.

Conceptual pseudocode:

```python
query = data["message"]
session_id = data.get("session_id", generated_id)
past_memory = recall_memory(session_id, query)
intent = detect_intent(query)

if intent == "party":
    answer = find_by_party(query)
elif intent == "education":
    answer = find_by_education(query)
elif intent == "compare":
    answer = compare_candidates(query)  # structured facts + LLM prose
elif intent == "semantic":
    answer = semantic_answer(query, memory_context=past_memory)
else:
    answer = find_candidate(query)

retain_memory(session_id, summary)
return jsonify(answer)
```

## 7. Intent routing

`backend/intent_router.py` contains `detect_intent(query)`. It is a rule-based, priority-ordered classifier. It lowercases the query and checks keyword lists and regular expressions. The first matching category wins.

| Intent | Example trigger | Internal handler |
| --- | --- | --- |
| `compare` | `compare`, `vs`, `versus`, `difference` | `compare_candidates()` plus Groq summary |
| `party` | Known party labels such as DMK, AIADMK, TVK | `find_by_party()` |
| `education` | Degree regex patterns such as BCA, MBA, PhD | `find_by_education()` |
| `male` / `female` | "male candidates" / "female candidates" | `find_by_gender()` |
| `constituency` | Known constituency names | `find_by_constituency()` |
| `semantic` | `summarize`, `affidavit`, `criminal`, `disclosure`, `explain` | `semantic_answer()` |
| `unknown` | No prior pattern matched | `find_candidate()` with fuzzy matching |

Order matters. For example, "Compare DMK candidates" matches both comparison and party terms. Comparison is checked first, so it is routed as a comparison.

The code recognizes a `richest` intent but the current `/chat` code does not implement a corresponding branch. `richest_candidates()` and `GET /top-assets` exist, so connecting it is a straightforward improvement.

## 8. Structured query path

The structured data is loaded from `backend/candidate_master_data.json`.

`backend/query_engine.py` supports:

- `find_candidate(query)`: cleans and normalizes the query, then uses RapidFuzz to match imperfect candidate names.
- `find_by_party(query)`: filters records by party.
- `find_by_education(query)`: identifies a requested degree and filters records.
- `find_by_constituency(query)`: filters constituency values.
- `find_by_gender(gender)`: filters gender.
- `compare_candidates(query)`: parses two names and returns their structured records.
- `richest_candidates(limit)`: sorts by total declared assets.

Structured retrieval is preferred for exact filters and comparison facts because it is deterministic, low-cost, and faster than vector retrieval plus an LLM.

For comparison, the system supplies structured values—party, constituency, education, assets, liabilities, criminal cases, occupation—to Groq and asks it to write a concise comparison. The LLM writes readable prose but should not invent facts.

## 9. OCR and structured extraction

The source affidavits are scanned PDFs. `backend/extract_pipeline.py`:

1. Converts PDFs to images using `pdf2image` at 300 DPI.
2. Calls Tesseract with `lang="eng+tam"`.
3. Saves page-level text and metadata such as source file, page number, candidate, party, and constituency.

The parser in `backend/affidavit_parser.py` uses section keywords and regex rules to extract fields such as education, contact information, assets, liabilities, and income-tax values into structured JSON.

Main risk: OCR and simple regex extraction are imperfect, particularly for Tamil tables, layouts, and financial figures. The product must advise users to verify consequential information against official source PDFs.

## 10. RAG fundamentals

RAG means Retrieval-Augmented Generation.

```text
Question → retrieve relevant affidavit evidence → provide evidence to LLM → grounded answer
```

The model is not asked to answer from general training knowledge. It receives relevant affidavit text as context and is instructed to answer only from that context. If the answer is missing, it should say so.

This improves factuality and traceability but does not eliminate errors. Bad OCR, poor chunking, weak retrieval, or a bad prompt can still lead to incorrect answers.

## 11. Embeddings

Embeddings are numerical vectors that represent the semantic meaning of text. Similar meanings are placed near each other in vector space.

The project uses `paraphrase-multilingual-MiniLM-L12-v2` for semantic search. Both affidavit sections and user queries must be embedded using the same model so they can be compared in the same vector space.

The multilingual model helps retrieve relevant Tamil or English material despite paraphrasing and language variation.

## 12. Semantic chunking and ChromaDB

Semantic chunking means grouping content by meaning rather than blindly splitting every N characters. Candidate affidavit material is handled as topic-specific documents such as personal details, education, criminal cases, income tax, and assets.

A ChromaDB record conceptually contains:

```text
Document: criminal-disclosure text
Embedding: vector representing the document meaning
Metadata: candidate, section, constituency, source file, and optionally page
```

At question time, `semantic_search.py`:

1. Embeds the user query.
2. Infers likely affidavit section from terms such as assets, criminal, education, or income.
3. Uses candidate fuzzy matching when possible.
4. Queries persistent ChromaDB collection `affidavits` for the top three matches.
5. Uses metadata filters for candidate and/or section when available.
6. Sends retrieved documents, metadata, memory context, and the question to Groq.

ChromaDB returns documents, metadata, and distance values. The response exposes source metadata such as candidate and section so the frontend can show retrieval evidence.

## 13. Hindsight conversational memory

Hindsight is separate from ChromaDB.

| Component | Stores | Purpose |
| --- | --- | --- |
| ChromaDB | Affidavit knowledge and embeddings | Retrieve official-document evidence for RAG. |
| Hindsight | Summaries of the user's session interactions | Recall conversational context for follow-up questions. |

The Hindsight client is initialized in `backend/memory.py` with the Hindsight API URL and `HINDSIGHT_API_KEY`. The memory bank is `candidate-rag`.

### When Flask recalls memory

At the beginning of every `/chat` request, Flask calls:

```python
past_memory = recall_memory(session_id, query)
```

`recall_memory()` calls the Hindsight SDK:

```python
client.recall(
    bank_id="candidate-rag",
    query=f"Session: {session_id}\nQuestion: {query}"
)
```

Hindsight returns relevant prior memory text. Flask joins it into `past_memory`.

Hindsight does not push data to Flask automatically. Flask actively asks for relevant memory on every chat request.

### When Flask stores memory

After processing a query, the backend calls `retain_memory()` directly or through helpers such as `remember_candidate()` and `remember_compare()`.

Example retained memory:

```text
Session: k8p3zq1m
Memory: User is interested in candidate MKStalin.
```

The memory includes session metadata, allowing the application to scope memories to the same conversational session.

### How recalled memory is used in answering

For semantic RAG, Flask passes `past_memory` into `semantic_answer()`. That function includes it in the Groq prompt:

```text
Previous context from this user's session:
User is interested in candidate MKStalin.

Context:
[retrieved affidavit sections]

Question:
What are his assets?
```

This helps the LLM interpret follow-up phrases such as "his assets," "her education," or "what about criminal cases?"

For comparisons, the backend similarly includes a memory block in the LLM prompt. For direct structured list/profile answers, memory may be recalled and retained but the response can come straight from JSON without using an LLM prompt.

### Hindsight and follow-up suggestions

Hindsight does **not** generate follow-up suggestions. Groq generates them; React displays them as clickable buttons. Hindsight becomes relevant only when a user sends a follow-up question using the same session ID.

### Current limitation

The RAG prompt gets recalled memory, but candidate filtering in `semantic_search.py` still tries to fuzzy-match a candidate from the current query. A pronoun-only query like "What are his assets?" may therefore have weaker retrieval even if the LLM prompt knows the earlier candidate. A strong next improvement is to extract the candidate from recalled memory and apply it as the ChromaDB metadata filter.

### What happens on browser close

The React session ID is lost after close or refresh because it is held only in JavaScript memory. Hindsight records previously retained memories remotely and the current code does not delete them automatically; however, a new page instance gets a new session ID and will not recall the old session's memories. Production needs authenticated IDs, retention limits, consent, and deletion controls.

## 14. LLM and answer generation

`backend/groq_client.py` creates a Groq client using `GROQ_API_KEY` and calls model `llama-3.3-70b-versatile` with low temperature.

The LLM is used for:

- Grounded answers from retrieved affidavit context.
- Natural-language comparison summaries based on structured fields.
- Contextual follow-up questions.
- General fallback responses.

For RAG, the prompt says to answer only using retrieved context, state when information is absent, and produce four follow-up questions. This prompt constraint is an important hallucination-control mechanism.

## 15. Example end-to-end follow-up

```text
1. User opens the app. React creates session ID k8p3zq1m.
2. User asks: "Tell me about MK Stalin."
3. React calls POST /chat with that message and ID.
4. Flask asks Hindsight for relevant memories; none exist yet.
5. Intent router chooses candidate lookup.
6. RapidFuzz finds MKStalin in structured JSON.
7. Flask responds and retains: "User is interested in candidate MKStalin."
8. React shows the answer and LLM-created follow-up buttons.
9. User sends: "What are his assets?" with the same ID.
10. Flask asks Hindsight; it returns MKStalin context.
11. Flask routes to semantic RAG, ChromaDB retrieves relevant affidavit material, and Groq sees the question, retrieved evidence, and past memory.
12. Flask returns answer, sources, and follow-up questions; then it retains a summary of the new interaction.
```

## 16. Deployment and stack

| Layer | Technology |
| --- | --- |
| Frontend | React, deployable on Vercel |
| API/orchestration | Flask, deployable with Gunicorn on Railway |
| OCR | Tesseract, Tamil + English |
| PDF rendering | pdf2image / Poppler |
| Structured matching | RapidFuzz and JSON records |
| Embeddings | multilingual Sentence Transformers MiniLM |
| Vector store | Persistent ChromaDB |
| LLM | Groq, Llama 3.3 70B Versatile |
| Conversation memory | Hindsight by Vectorize |

## 17. Important limitations and honest answers

- OCR quality is the largest data-quality risk, particularly for Tamil tables, layout, and monetary values.
- The structured parser is rule and regex based; it needs validation before being used for high-stakes claims.
- Current data scope is limited to the available Kolathur candidate PDFs.
- Current intent routing is keyword/rule based and can miss phrasing or Tamil variants.
- The frontend's random session ID is not authenticated and does not survive refresh/close.
- Recalled Hindsight context helps answer generation but is not yet fully used to enforce candidate filtering in pronoun-only RAG follow-ups.
- The router detects a richest-assets intent, but the `/chat` route lacks the corresponding handler.

## 18. High-value improvements

1. Save session IDs in browser session storage or use authenticated user IDs.
2. Add memory expiry, deletion, consent, and privacy controls.
3. Resolve pronouns/remembered candidate before ChromaDB retrieval, not only in the LLM prompt.
4. Improve OCR with preprocessing, layout-aware OCR, and table extraction.
5. Attach exact PDF page citations and source-PDF links to every answer.
6. Add numeric validation and a human-review workflow for fields extracted from OCR.
7. Add Tamil patterns or a hybrid classifier to intent routing.
8. Connect the existing `richest` intent to `richest_candidates()` within `/chat`.
9. Expand ingestion to more constituencies and use background jobs/observability for scale.

## 19. Interview questions

1. Give a one-minute overview of the Candidate Compliance Agent.
2. Why is this a hybrid RAG system instead of a pure RAG system?
3. Explain the offline ingestion pipeline from PDF to ChromaDB.
4. What is OCR, and why did you use 300 DPI plus Tamil and English language packs?
5. What are embeddings, and why must documents and queries use the same embedding model?
6. What does ChromaDB store, and how does metadata filtering improve retrieval?
7. What is semantic chunking, and why is it better than only fixed-size chunks for affidavits?
8. Explain exactly what happens after React calls `sendMessage()`.
9. Does the intent router route users to different URLs? Explain the difference between `/chat` routing and direct REST endpoints.
10. How does the rule-based intent router classify a question, and why does priority order matter?
11. What is the difference between ChromaDB and Hindsight in this system?
12. When does Flask call Hindsight recall, what does it send, and what does it receive?
13. How is recalled Hindsight memory inserted into an LLM prompt?
14. Does Hindsight generate follow-up questions? If not, which component does?
15. How does the current session ID work, and what happens after refresh or close?
16. Why can a pronoun-only query still be unreliable in the current RAG implementation?
17. How do you reduce hallucinations in this system?
18. What are the most serious current limitations?
19. How would you scale from 35 candidates to thousands?
20. What would you improve first for production readiness?

## 20. Concise final pitch

"The project turns scanned public election affidavits into a conversational, bilingual compliance-information assistant. It uses OCR to extract text, structured data for exact queries, ChromaDB RAG for document questions, Groq for grounded natural-language answers, and Hindsight for session-level conversational context. The key design decision is hybrid routing: deterministic questions use structured data, while nuanced affidavit questions use retrieved evidence and an LLM." 
