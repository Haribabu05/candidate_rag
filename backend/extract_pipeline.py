import re
import fitz
import json
from pathlib import Path


# Detect mostly-English text blocks
def is_english_page(text):

    ascii_count = sum(
        1 for c in text
        if ord(c) < 128 and c.isprintable()
    )

    return ascii_count / max(len(text), 1) > 0.6


# Extract structured metadata
def extract_sections(full_text):

    sections = {
        "assets_movable": "",
        "assets_immovable": "",
        "liabilities": "",
        "education": "",
        "criminal_cases": "",
        "income_tax": "",
        "pan": ""
    }

    # Keep only English-heavy blocks
    english_text = "\n".join(
        block for block in full_text.split("\n\n")
        if is_english_page(block)
    )

    # PAN extraction
    pan_match = re.search(
        r'[A-Z]{5}[0-9]{4}[A-Z]',
        english_text
    )

    if pan_match:
        sections["pan"] = pan_match.group()

    # Income tax extraction
    income_lines = re.findall(
        r'(20\d\d[-–]\d{2,4})[^\d]*([\d,]+)\s*[-/]?',
        english_text
    )

    if income_lines:
        sections["income_tax"] = str(income_lines)

    # Education extraction
    edu_keywords = [
        "B.A", "B.Sc", "B.Com", "B.E",
        "M.A", "M.Sc", "MBA", "LLB",
        "SSLC", "HSC", "Graduate",
        "Post Graduate", "Literate",
        "Illiterate", "10th", "12th",
        "Diploma", "degree", "school"
    ]

    for keyword in edu_keywords:

        pattern = rf'.{{0,80}}{re.escape(keyword)}.{{0,80}}'

        matches = re.findall(
            pattern,
            english_text,
            re.IGNORECASE
        )

        if matches:
            sections["education"] += (
                " | ".join(matches) + "\n"
            )

    # Criminal case extraction
    criminal_keywords = [
        "FIR", "IPC", "case", "criminal",
        "acquitted", "convicted",
        "pending", "chargesheet", "Section"
    ]

    for keyword in criminal_keywords:

        pattern = rf'.{{0,100}}{re.escape(keyword)}.{{0,100}}'

        matches = re.findall(
            pattern,
            english_text,
            re.IGNORECASE
        )

        if matches:
            sections["criminal_cases"] += (
                " | ".join(matches) + "\n"
            )

    # Asset extraction
    asset_matches = re.findall(
        r'(.{0,60}(?:Rs\.?|₹|\bINR\b).{0,60})',
        english_text,
        re.IGNORECASE
    )

    if asset_matches:

        sections["assets_movable"] = "\n".join(
            asset_matches[:20]
        )

    return sections


# Process one PDF
def extract_pdf(
    pdf_path,
    constituency,
    candidate,
    party,
    affidavit_no
):

    doc = fitz.open(pdf_path)

    full_text = ""

    pages = []

    for i, page in enumerate(doc):

        text = page.get_text().strip()

        if text:

            full_text += text + "\n\n"

            pages.append({
                "text": text,
                "page": i + 1,
                "metadata": {
                    "constituency": constituency,
                    "candidate": candidate,
                    "party": party,
                    "affidavit_no": affidavit_no,
                    "source_file": str(pdf_path)
                }
            })

    # Extract metadata
    sections = extract_sections(full_text)

    # Attach metadata to every page
    for p in pages:

        p["metadata"]["pan"] = (
            sections["pan"]
        )

        p["metadata"]["education"] = (
            sections["education"][:300]
        )

        p["metadata"]["criminal_cases"] = (
            sections["criminal_cases"][:300]
        )

        p["metadata"]["income_tax"] = (
            sections["income_tax"][:300]
        )

        p["metadata"]["assets_summary"] = (
            sections["assets_movable"][:300]
        )

    return pages


# Process all PDFs
def process_all(data_dir="data"):

    all_pages = []

    data_path = Path(data_dir)

    for pdf_file in data_path.glob("*.pdf"):

        parts = pdf_file.stem.split("-")

        if len(parts) >= 3:

            candidate = parts[0]
            party = parts[1]
            affidavit = parts[2]

        else:

            candidate = pdf_file.stem
            party = "UNKNOWN"
            affidavit = "1"

        pages = extract_pdf(
            pdf_file,
            "KOLATHUR",
            candidate,
            party,
            affidavit
        )

        all_pages.extend(pages)

        print(
            f"✓ {pdf_file.name} → {len(pages)} pages"
        )

    return all_pages


# Run extraction pipeline
pages = process_all()

print(f"\nTotal pages extracted: {len(pages)}")


# Save structured JSON
with open(
    "extracted_pages.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        pages,
        f,
        ensure_ascii=False,
        indent=2
    )


# Save full affidavit text
full_document_text = "\n\n".join(
    page["text"] for page in pages
)

with open(
    "full_affidavit.txt",
    "w",
    encoding="utf-8"
) as f:

    f.write(full_document_text)

print("\nSaved full affidavit text")


# Debug metadata
meta = pages[0]["metadata"]

print("\n=== METADATA CHECK ===")

print(f"Candidate  : {meta['candidate']}")
print(f"Party      : {meta['party']}")
print(f"PAN        : {meta['pan']}")

print("\n=== EDUCATION ===")
print(meta["education"])

print("\n=== CRIMINAL CASES ===")
print(meta["criminal_cases"])

print("\n=== INCOME TAX ===")
print(meta["income_tax"])

print("\n=== ASSETS ===")
print(meta["assets_summary"])


# Debug sample text
print("\n=== RAW TEXT PAGE 3 ===")

print(
    pages[2]["text"][:1000]
)