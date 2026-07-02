

import json
import re
from collections import defaultdict
import chromadb
from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────────────────────
MASTER_JSON   = "candidate_master_data.json"
PAGES_JSON    = "extracted_pages.json"
CHROMA_PATH   = "./chroma_db"
COLLECTION    = "affidavits"
EMBED_MODEL   = "paraphrase-multilingual-MiniLM-L12-v2"

# ── Helpers ───────────────────────────────────────────────────────────────────
def clean(text: str) -> str:
    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 3]
    return re.sub(r"\s+", " ", " ".join(lines)).strip()

def pages_in_range(raw_pages, start, end):
    return " ".join(
        clean(p["text"]) for p in raw_pages
        if start <= p["metadata"]["page"] <= end
    )

# ── Document builder ──────────────────────────────────────────────────────────
def build_docs(c: dict, raw_pages: list) -> list[dict]:
    name  = c["candidate"]
    party = c["party"]
    const = c["constituency"]

    docs = []

    # 1 — Identity
    docs.append({
        "section": "identity",
        "text": f"""Candidate: {name}
Party: {party}
Constituency: {const}
Section: Identity and Contact Information

Phone: {", ".join(c["phones"]) if c["phones"] else "Not available"}
Email: {", ".join(c["emails"]) if c["emails"] else "Not available"}
PAN: {", ".join(c["pan_ids"]) if c["pan_ids"] else "Not available"}
Spouse: {c["spouse"] or "Not available"}
Dependents: {c["dependents"]}
Occupation: {c["occupation"] or "Not available"}"""
    })

    # 1.5  — Personal Details

    personal = pages_in_range(raw_pages, 1, 2)

    docs.append({
        "section": "personal_details",
        "text": f"""Candidate: {name}
    Party: {party}
    Constituency: {const}
    Section: Personal Details

    {personal[:2000]}"""
    })




    # 2 — Education
    edu = (c["education"] or {}).get("degree", "Not extracted")
    docs.append({
        "section": "education",
        "text": f"""Candidate: {name}
Party: {party}
Section: Education

Highest Qualification: {edu}
Raw text: {pages_in_range(raw_pages, 13, 15)[:500]}"""
    })

    # 3 — Criminal cases (structured)
    cc      = c["criminal_cases"] or {}
    pending = cc.get("pending", 0)
    convicted = cc.get("convicted", 0)
    docs.append({
        "section": "criminal_cases",
        "text": f"""Candidate: {name}
Party: {party}
Section: Criminal Cases

Pending Cases: {pending}
Convicted Cases: {convicted}
Summary: {"No criminal record" if pending == 0 and convicted == 0
          else f"{pending} pending case(s), {convicted} conviction(s)"}"""
    })

    # 4 — Criminal detail (raw OCR pages 4–6)
    crim_raw = pages_in_range(raw_pages, 4, 6)
    docs.append({
        "section": "criminal_detail",
        "text": f"""Candidate: {name}
Party: {party}
Section: Criminal Cases Detail (from affidavit)

{crim_raw[:2000]}"""
    })

    # 5 — Income tax
    it = c["income_tax"] or {}
    if it:
        it_lines = "\n".join(
            f"  FY {yr}: Rs.{amt:,}" for yr, amt in sorted(it.items())
        )
        it_block = f"Income declared per financial year:\n{it_lines}"
    else:
        it_block = "Income tax records not extracted from this affidavit."
    docs.append({
        "section": "income_tax",
        "text": f"""Candidate: {name}
Party: {party}
Section: Income Tax

{it_block}"""
    })

    # 6 — Assets & liabilities (raw OCR pages 7–15)
    asset_raw = pages_in_range(raw_pages, 7, 15)
    docs.append({
        "section": "assets",
        "text": f"""Candidate: {name}
Party: {party}
Section: Assets and Liabilities

{asset_raw[:3000]}"""
    })

    # Attach metadata to every doc
    for d in docs:
        d["candidate"]    = name
        d["party"]        = party
        d["constituency"] = const

    return docs

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("Loading data...")
    with open(MASTER_JSON, encoding="utf-8") as f:
        master = json.load(f)
    with open(PAGES_JSON, encoding="utf-8") as f:
        pages = json.load(f)

    # Group pages by candidate
    by_candidate = defaultdict(list)
    for p in pages:
        by_candidate[p["metadata"]["candidate"]].append(p)

    # Build semantic documents
    all_docs = []
    for name, c in master.items():
        all_docs.extend(build_docs(c, by_candidate[name]))

    print(f"Total semantic documents: {len(all_docs)}")

    # Init ChromaDB
    print(f"Connecting to ChromaDB at {CHROMA_PATH}...")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        client.delete_collection(COLLECTION)
        print("Deleted existing collection.")
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"}
    )

    # Embed
    print(f"Loading embedding model: {EMBED_MODEL}")
    model = SentenceTransformer(EMBED_MODEL)

    texts = [d["text"] for d in all_docs]
    print("Embedding...")
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True).tolist()

    # Store
    collection.add(
        documents=texts,
        embeddings=embeddings,
        metadatas=[{
            "candidate":    d["candidate"],
            "party":        d["party"],
            "constituency": d["constituency"],
            "section":      d["section"],
        } for d in all_docs],
        ids=[f"{d['candidate']}_{d['section']}" for d in all_docs],
    )

    print(f"\nDone! {len(all_docs)} documents stored in ChromaDB.")
    print("Sections per candidate: identity, personal_details,education, criminal_cases, criminal_detail, income_tax, assets")

if __name__ == "__main__":
    main()