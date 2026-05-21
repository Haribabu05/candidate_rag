import json
import re
import chromadb

from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ==========================================
# LOAD EXTRACTED PAGES
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

# delete old collection if exists
try:
    client.delete_collection(
        "candidate_affidavits"
    )
except:
    pass

collection = client.get_or_create_collection(
    "candidate_affidavits"
)

# ==========================================
# TEXT SPLITTER
# ==========================================
splitter = RecursiveCharacterTextSplitter(
    chunk_size=700,
    chunk_overlap=100
)

# ==========================================
# HELPERS
# ==========================================
def clean_text(text):

    return " ".join(text.split())


def detect_section(text):

    text_lower = text.lower()

    if (
        "income" in text_lower
        or "tax return" in text_lower
    ):

        return "income"

    elif (
        "asset" in text_lower
        or "liabilit" in text_lower
    ):

        return "assets"

    elif "criminal" in text_lower:

        return "criminal"

    elif "pan" in text_lower:

        return "pan"

    elif "party" in text_lower:

        return "party"

    else:

        return "general"


def extract_pan(text):

    pattern = r"[A-Z]{5}[0-9]{4}[A-Z]"

    match = re.search(pattern, text)

    if match:

        return match.group(0)

    return "Unknown"


def extract_recent_income(text):

    income_patterns = [

        r"Rs\.?\s?[\d,]+\/?-?",
        r"Rs\s?[\d,]+",
        r"₹\s?[\d,]+"
    ]

    for pattern in income_patterns:

        matches = re.findall(
            pattern,
            text
        )

        if matches:

            return matches[0]

    return "Unknown"


# ==========================================
# STORE UNIQUE CANDIDATE SUMMARY
# ==========================================
candidate_master_data = {}

# ==========================================
# INGESTION
# ==========================================
doc_id = 0

for page in pages:

    metadata = page.get(
        "metadata",
        {}
    )

    candidate = metadata.get(
        "candidate",
        "Unknown"
    )

    party = metadata.get(
        "party",
        "Unknown"
    )

    constituency = metadata.get(
        "constituency",
        "Unknown"
    )

    page_no = metadata.get(
        "page",
        "Unknown"
    )

    raw_text = page.get(
        "text",
        ""
    )

    text = clean_text(raw_text)

    # ======================================
    # EXTRACT STRUCTURED DATA
    # ======================================
    pan_id = extract_pan(text)

    recent_income = extract_recent_income(
        text
    )

    # ======================================
    # STORE MASTER CANDIDATE DATA
    # ======================================
    if candidate not in candidate_master_data:

        candidate_master_data[candidate] = {

            "candidate": candidate,

            "party": party,

            "constituency": constituency,

            "pan_id": pan_id,

            "recent_income": recent_income
        }

    else:

        # update missing PAN
        if (
            candidate_master_data[candidate]["pan_id"]
            == "Unknown"
            and pan_id != "Unknown"
        ):

            candidate_master_data[candidate][
                "pan_id"
            ] = pan_id

        # update income
        if (
            candidate_master_data[candidate][
                "recent_income"
            ] == "Unknown"
            and recent_income != "Unknown"
        ):

            candidate_master_data[candidate][
                "recent_income"
            ] = recent_income

    # ======================================
    # SPLIT INTO CHUNKS
    # ======================================
    chunks = splitter.split_text(text)

    for chunk in chunks:

        section = detect_section(chunk)

        embedding = model.encode(
            chunk
        ).tolist()

        chunk_metadata = {

            "candidate": candidate,

            "party": party,

            "constituency": constituency,

            "page": str(page_no),

            "section": section,

            "pan_id": pan_id,

            "recent_income": recent_income
        }

        collection.add(

            documents=[chunk],

            embeddings=[embedding],

            metadatas=[chunk_metadata],

            ids=[f"doc_{doc_id}"]
        )

        doc_id += 1

# ==========================================
# STORE STRUCTURED CANDIDATE DATA
# ==========================================
with open(
    "candidate_master_data.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        candidate_master_data,
        f,
        indent=4,
        ensure_ascii=False
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