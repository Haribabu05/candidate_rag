"""
semantic_search.py — ChromaDB retrieval module for the Flask app.
"""

import re
import chromadb
from sentence_transformers import SentenceTransformer
from query_engine import find_candidate
import os

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "affidavits"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
TOP_K = 3

print("Loading embedding model for semantic search...")
_embedder = SentenceTransformer(EMBED_MODEL)

print("Connecting to ChromaDB...")
_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _client.get_collection(COLLECTION_NAME)
print(f"ChromaDB ready: {_collection.count()} documents loaded.")


def semantic_search(query: str, candidate: str = None, section: str = None, top_k: int = TOP_K):
    query_embedding = _embedder.encode([query])[0].tolist()

    where = {}
    if candidate and section:
        where = {"$and": [{"candidate": candidate}, {"section": section}]}
    elif candidate:
        where = {"candidate": candidate}
    elif section:
        where = {"section": section}

    kwargs = dict(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    if where:
        kwargs["where"] = where

    return _collection.query(**kwargs)


def _parse_answer_and_follow_ups(raw_response: str):
    """
    Parse a raw Gemini response of the form:

        ANSWER:
        <answer text>
        FOLLOW_UP_QUESTIONS:
        1. <question 1>
        2. <question 2>
        ...

    Falls back gracefully if the expected markers are missing or the
    numbering format doesn't exactly match "N." / "N)".
    """
    if "FOLLOW_UP_QUESTIONS:" not in raw_response:
        return raw_response.strip(), []

    parts = raw_response.split("FOLLOW_UP_QUESTIONS:", 1)
    answer_part = parts[0].replace("ANSWER:", "").strip()
    follow_up_part = parts[1].strip()

    follow_ups = []
    # Matches "1.", "1)", "1 -", etc. at the start of a line, with anything after it.
    line_pattern = re.compile(r"^\s*\d+\s*[.)-]?\s*(.+)$")

    for line in follow_up_part.splitlines():
        line = line.strip()
        if not line:
            continue
        match = line_pattern.match(line)
        if match:
            question = match.group(1).strip()
            if question:
                follow_ups.append(question)
        else:
            # Line doesn't look numbered but still has content — keep it
            # rather than silently dropping a follow-up question.
            follow_ups.append(line)

    return answer_part, follow_ups


def semantic_answer(query: str, known_candidates: list, ask_gemini_fn, memory_context: str = "") -> dict:
    """
    Full semantic RAG flow with Hindsight memory context injected into prompt.
    Now also returns model-generated follow-up questions.
    """
    section = None
    q = query.lower()

    if "asset" in q:
        section = "assets"
    elif "education" in q:
        section = "education"
    elif "criminal" in q:
        section = "criminal_cases"
    elif "income" in q:
        section = "income_tax"
    elif any(w in q for w in ["age", "address", "father", "mother", "wife", "spouse"]):
        section = "personal_details"

    candidate_data = find_candidate(query)
    candidate = candidate_data["candidate"] if candidate_data else None

    print("FUZZY CANDIDATE =", candidate)

    results = semantic_search(query=query, candidate=candidate, section=section)
    docs = results["documents"][0]
    metas = results["metadatas"][0]

    print("=" * 80)
    print("RETRIEVED DOCUMENTS")
    for i, (doc, meta) in enumerate(zip(docs, metas), start=1):
        print(f"\nRESULT {i}")
        print(meta)
        print(doc[:500])
    print("=" * 80)

    if not docs:
        return {
            "answer": "No relevant information found in the affidavits.",
            "source": "semantic",
            "sources": [],
            "follow_ups": []
        }

    context_parts = []
    for doc, meta in zip(docs, metas):
        context_parts.append(f"[{meta['candidate']} — {meta['section']}]\n{doc}")
    context = "\n\n---\n\n".join(context_parts)

    memory_block = f"\nPrevious context from this user's session:\n{memory_context}\n" if memory_context else ""

    prompt = f"""You are answering questions about Tamil Nadu election candidate affidavits.
The context below is in Tamil and English, extracted from official affidavits.
Answer ONLY using the information in the context. If the answer is not present, say so clearly.
Be concise and factual.
{memory_block}
Context:
{context}

Question: {query}

Respond in this exact format:
ANSWER:
<your answer here>
FOLLOW_UP_QUESTIONS:
1. <question 1>
2. <question 2>
3. <question 3>
4. <question 4>
"""

    raw_response = ask_gemini_fn(prompt)
    answer_text, follow_ups = _parse_answer_and_follow_ups(raw_response)

    sources = [
        {"candidate": m["candidate"], "section": m["section"]}
        for m in metas
    ]

    return {
        "answer": answer_text,
        "source": "semantic",
        "sources": sources,
        "follow_ups": follow_ups
    }