"""
semantic_search.py — ChromaDB retrieval module for the Flask app.

Place this file in the same folder as app.py.
Import it in app.py with:
    from semantic_search import semantic_answer
"""

import chromadb
from sentence_transformers import SentenceTransformer

#importing function find_candidate from query_engine.py for implementing rapidfuzzy search
from query_engine import find_candidate

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "affidavits"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
TOP_K = 3

# ── Load once at import time (not per-request) ─────────────────────────────────
print("Loading embedding model for semantic search...")
_embedder = SentenceTransformer(EMBED_MODEL)

print("Connecting to ChromaDB...")
_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _client.get_collection(COLLECTION_NAME)
print(f"ChromaDB ready: {_collection.count()} documents loaded.")



def semantic_search(query: str, candidate: str = None, section: str = None, top_k: int = TOP_K):
    """
    Run vector search against ChromaDB.
    Optionally filter by candidate name and/or section
    (section options: identity, education, criminal_cases,
     criminal_detail, income_tax, assets)
    """
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




def semantic_answer(query: str, known_candidates: list, ask_gemini_fn) -> dict:
    """
    Full semantic RAG flow:
    1. Try to detect candidate name in query
    2. Retrieve relevant chunks from ChromaDB
    3. Build context and ask Gemini
    4. Return answer + sources

    ask_gemini_fn: pass in your existing ask_gemini(prompt) function
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

    elif "age" in q:
        section = "personal_details"

    elif "address" in q:
        section = "personal_details"

    elif "father" in q:
        section = "personal_details"

    elif "mother" in q:
        section = "personal_details"

    elif "wife" in q:
        section = "personal_details"

    elif "spouse" in q:
        section = "personal_details"

    candidate_data = find_candidate(query)

    candidate = None

    if candidate_data:
        candidate = candidate_data["candidate"]

    print("FUZZY CANDIDATE =", candidate)

    results = semantic_search(
        query=query,
        candidate=candidate,
        section=section
    )
    #docs = results["documents"][0]
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
        context_parts.append(
            f"[{meta['candidate']} — {meta['section']}]\n{doc}"
        )
    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""You are answering questions about Tamil Nadu election candidate affidavits.
The context below is in Tamil and English, extracted from official affidavits.
Answer ONLY using the information in the context. If the answer is not present, say so clearly.
Be concise and factual.

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