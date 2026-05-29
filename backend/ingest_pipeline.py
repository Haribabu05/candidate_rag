# ==========================================
# FILE: backend/ingest_pipeline.py
# ==========================================

import re
import json
import chromadb

from sentence_transformers import (
    SentenceTransformer
)

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

# ==========================================
# LOAD OCR DATA
# ==========================================

with open(
    "extracted_pages_paddle.json",
    "r",
    encoding="utf-8"
) as f:

    extracted_pages = json.load(f)

# ==========================================
# EMBEDDING MODEL
# ==========================================

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

# ==========================================
# CHROMADB
# ==========================================

client = chromadb.PersistentClient(
    path="chroma_db"
)

# DELETE OLD COLLECTION
try:

    client.delete_collection(
        "candidate_affidavits"
    )

except:
    pass

collection = client.create_collection(
    "candidate_affidavits"
)

# ==========================================
# TEXT SPLITTER
# ==========================================

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

# ==========================================
# REGEX PATTERNS
# ==========================================

PAN_REGEX = (
    r"[A-Z]{5}[0-9]{4}[A-Z]"
)

EMAIL_REGEX = (
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
)

PHONE_REGEX = (
    r"\b\d{10}\b"
)

MONEY_REGEX = (
    r"\b\d{1,3}(?:,\d{2,3})+\b"
)

# ==========================================
# STRUCTURED STORAGE
# ==========================================

# ==========================================
# IMPORT PARSER
# ==========================================

from affidavit_parser import (
    parse_candidate_pages
)

# ==========================================
# GROUP PAGES BY CANDIDATE
# ==========================================

candidate_pages = {}

for page in extracted_pages:

    candidate = (
        page["metadata"]["candidate"]
    )

    if candidate not in candidate_pages:

        candidate_pages[
            candidate
        ] = []

    candidate_pages[
        candidate
    ].append(page)

# ==========================================
# PARSE CANDIDATES
# ==========================================

candidate_master_data = {}

for candidate, pages in (
    candidate_pages.items()
):

    parsed = parse_candidate_pages(

        candidate,
        pages
    )

    candidate_master_data[
        candidate
    ] = parsed

# ==========================================
# VECTOR STORAGE
# ==========================================

doc_id = 0

for page in extracted_pages:

    text = page["text"]

    metadata = page["metadata"]

    candidate = metadata["candidate"]

    party = metadata["party"]

    constituency = (
        metadata["constituency"]
    )

    page_no = metadata["page"]

    source_file = metadata[
        "source_file"
    ]

    chunks = splitter.split_text(
        text
    )

    for chunk_num, chunk in enumerate(chunks):

        embedding = model.encode(
            chunk
        ).tolist()

        chunk_id = (
            f"{candidate}_"
            f"{page_no}_"
            f"{chunk_num}"
        )

        collection.add(

            documents=[chunk],

            embeddings=[embedding],

            metadatas=[{

                "candidate": candidate,

                "party": party,

                "constituency": constituency,

                "page": page_no,

                "source_file": source_file
            }],

            ids=[chunk_id]
        )

        doc_id += 1

# ==========================================
# SAVE STRUCTURED DB
# ==========================================

with open(
    "candidate_master_data.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(

        candidate_master_data,

        f,

        ensure_ascii=False,

        indent=2
    )

# ==========================================
# DONE
# ==========================================

print(
    f"Stored {doc_id} chunks in ChromaDB"
)

print(
    f"Stored structured data for "
    f"{len(candidate_master_data)} candidates"
)