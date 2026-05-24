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
    "extracted_pages.json",
    "r",
    encoding="utf-8"
) as f:

    pages = json.load(f)

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

candidate_master_data = {}

# ==========================================
# CHUNK STORAGE
# ==========================================

doc_id = 0

# ==========================================
# PROCESS PAGES
# ==========================================

for page in pages:

    text = page["text"]

    metadata = page["metadata"]

    candidate = metadata["candidate"]

    party = metadata["party"]

    constituency = metadata["constituency"]

    page_no = metadata["page"]

    source_file = metadata["source_file"]

    # ======================================
    # CREATE CANDIDATE OBJECT
    # ======================================

    if candidate not in candidate_master_data:

        candidate_master_data[candidate] = {

            "candidate": candidate,

            "party": party,

            "constituency": constituency,

            "pan_ids": [],

            "emails": [],

            "phones": [],

            "income_values": [],

            "source_files": []
        }

    # ======================================
    # REGEX EXTRACTION
    # ======================================

    pans = re.findall(
        PAN_REGEX,
        text
    )

    emails = re.findall(
        EMAIL_REGEX,
        text
    )

    phones = re.findall(
        PHONE_REGEX,
        text
    )

    money_values = re.findall(
        MONEY_REGEX,
        text
    )

    cleaned_money_values = []

for value in money_values:

    digits_only = value.replace(",", "")

    if len(digits_only) >= 5:

        cleaned_money_values.append(value)


    # ======================================
    # STORE STRUCTURED DATA
    # ======================================

    candidate_master_data[
        candidate
    ]["pan_ids"].extend(pans)

    candidate_master_data[
        candidate
    ]["emails"].extend(emails)

    candidate_master_data[
        candidate
    ]["phones"].extend(phones)

    candidate_master_data[
        candidate
    ]["income_values"].extend(
        cleaned_money_values
    )

    candidate_master_data[
        candidate
    ]["source_files"].append(
        source_file
    )

    # ======================================
    # REMOVE DUPLICATES
    # ======================================

    for key in [

        "pan_ids",

        "emails",

        "phones",

        "income_values",

        "source_files"
    ]:

        candidate_master_data[
            candidate
        ][key] = list(

            set(

                candidate_master_data[
                    candidate
                ][key]
            )
        )

    # ======================================
    # CHUNKING
    # ======================================

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