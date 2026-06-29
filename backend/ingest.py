"""
ingest.py — Run once to chunk + embed + store all affidavit pages into ChromaDB

Install deps first:
    pip install chromadb sentence-transformers

Usage:
    python ingest.py --input extracted_pages.json --db ./chroma_db
"""

import json
import argparse
import re
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# ─── Config ───────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"  # Tamil + English
CHUNK_SIZE = 400       # tokens (approx — we use words as proxy)
CHUNK_OVERLAP = 50     # words overlap between consecutive chunks
COLLECTION_NAME = "affidavits"

# ─── Text cleaning ────────────────────────────────────────────────────────────
def clean_text(text: str) -> str:
    """Remove OCR noise: very short lines, excessive whitespace."""
    lines = text.split("\n")
    lines = [l.strip() for l in lines if len(l.strip()) > 3]
    text = " ".join(lines)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ─── Chunking ─────────────────────────────────────────────────────────────────
def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """
    Split text into overlapping word-based chunks.
    Returns list of chunk strings.
    """
    words = text.split()
    if len(words) <= chunk_size:
        return [text]  # short enough — return as single chunk

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start += chunk_size - overlap  # slide with overlap

    return chunks

# ─── Main ingestion ───────────────────────────────────────────────────────────
def ingest(input_path: str, db_path: str):
    print(f"Loading data from {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        pages = json.load(f)

    print(f"Total pages: {len(pages)}")

    # Load embedding model
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Init ChromaDB
    client = chromadb.PersistentClient(path=db_path)

    # Delete existing collection if re-running
    try:
        client.delete_collection(COLLECTION_NAME)
        print("Deleted existing collection.")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    all_chunks = []
    all_metadatas = []
    all_ids = []

    chunk_id = 0
    skipped = 0

    for page in pages:
        raw_text = page.get("text", "")
        metadata = page.get("metadata", {})

        text = clean_text(raw_text)
        if len(text) < 50:  # skip nearly empty pages
            skipped += 1
            continue

        chunks = chunk_text(text)

        for i, chunk in enumerate(chunks):
            
            header = f"""
            
            Candidate: {metadata.get('candidate','')}
            Party: {metadata.get('party','')}
            Constituency: {metadata.get('constituency','')}
            Page: {metadata.get('page',0)}

            """

            chunk = header + "\n" + chunk

            all_chunks.append(chunk)

            all_metadatas.append({
                "candidate": metadata.get("candidate", ""),
                "party": metadata.get("party", ""),
                "constituency": metadata.get("constituency", ""),
                "page": metadata.get("page", 0),
                "source_file": metadata.get("source_file", ""),
                "chunk_index": i,
            })
            all_ids.append(f"chunk_{chunk_id}")
            chunk_id += 1

    print(f"Total chunks to embed: {len(all_chunks)} (skipped {skipped} empty pages)")

    # Embed in batches of 64
    BATCH = 64
    all_embeddings = []
    for i in range(0, len(all_chunks), BATCH):
        batch = all_chunks[i:i+BATCH]
        embeddings = model.encode(batch, show_progress_bar=False).tolist()
        all_embeddings.extend(embeddings)
        print(f"  Embedded {min(i+BATCH, len(all_chunks))}/{len(all_chunks)}")

    # Store in ChromaDB in batches
    for i in range(0, len(all_chunks), BATCH):
        collection.add(
            documents=all_chunks[i:i+BATCH],
            embeddings=all_embeddings[i:i+BATCH],
            metadatas=all_metadatas[i:i+BATCH],
            ids=all_ids[i:i+BATCH],
        )

    print(f"\nDone! {len(all_chunks)} chunks stored in {db_path}")
    print(f"Collection: '{COLLECTION_NAME}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="extracted_pages.json")
    parser.add_argument("--db", default="./chroma_db")
    args = parser.parse_args()
    ingest(args.input, args.db)