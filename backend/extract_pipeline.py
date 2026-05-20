import fitz
import json
from pathlib import Path

all_pages = []

data_path = Path("data")

for constituency_folder in data_path.iterdir():

    if not constituency_folder.is_dir():
        continue

    constituency = constituency_folder.name

    for pdf_file in constituency_folder.glob("*.pdf"):

        parts = pdf_file.stem.split("-")

        candidate = parts[0]
        party = parts[1] if len(parts) > 1 else "UNKNOWN"

        doc = fitz.open(pdf_file)

        for i, page in enumerate(doc):

            text = page.get_text().strip()

            if text:

                all_pages.append({
                    "text": text,
                    "metadata": {
                        "candidate": candidate,
                        "party": party,
                        "constituency": constituency,
                        "page": i + 1,
                        "source": str(pdf_file)
                    }
                })

        print(f"✓ {pdf_file.name}")

with open("extracted_pages.json", "w", encoding="utf-8") as f:
    json.dump(all_pages, f, ensure_ascii=False, indent=2)

print(f"\nStored {len(all_pages)} pages")