"""
semantic_search.py — ChromaDB retrieval module for the Flask app.
"""

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


def semantic_answer(query: str, known_candidates: list, ask_gemini_fn, memory_context: str = "") -> dict:
    """
    Full semantic RAG flow with Hindsight memory context injected into prompt.
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
            "sources": []
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

Answer:"""

    answer_text = ask_gemini_fn(prompt)

    sources = [
        {"candidate": m["candidate"], "section": m["section"]}
        for m in metas
    ]

    return {
        "answer": answer_text,
        "source": "semantic",
        "sources": sources
    }