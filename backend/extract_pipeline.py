# ==========================================
# FILE: backend/extract_pipeline.py
# ==========================================

import os
import json
import pytesseract

from pdf2image import convert_from_path

# ==========================================
# TESSERACT CONFIG
# ==========================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# ==========================================
# CONFIG
# ==========================================

PDF_FOLDER = r"data\KOLATHUR"

OUTPUT_FILE = "extracted_pages.json"

POPPLER_PATH = r"C:\poppler\Library\bin"

# ==========================================
# STORAGE
# ==========================================

all_pages = []

# ==========================================
# PROCESS PDFs
# ==========================================

for filename in os.listdir(PDF_FOLDER):

    if not filename.endswith(".pdf"):
        continue

    pdf_path = os.path.join(
        PDF_FOLDER,
        filename
    )

    print(f"Processing {filename}")

    try:

        images = convert_from_path(
            pdf_path,
            dpi=300,
            poppler_path=POPPLER_PATH
        )

        # ==================================
        # FILE METADATA
        # ==================================

        parts = filename.replace(
            ".pdf",
            ""
        ).split("-")

        candidate = (
            parts[0]
            if len(parts) > 0
            else "Unknown"
        )

        party = (
            parts[1]
            if len(parts) > 1
            else "Unknown"
        )

        # ==================================
        # OCR EACH PAGE
        # ==================================

        for page_num, image in enumerate(images):

            text = pytesseract.image_to_string(
                image,
                lang="eng"
            )

            page_data = {

                "text": text,

                "metadata": {

                    "source_file": filename,

                    "page": page_num + 1,

                    "candidate": candidate,

                    "party": party,

                    "constituency": "KOLATHUR"
                }
            }

            all_pages.append(page_data)

        print(f"✓ {filename}")

    except Exception as e:

        print(
            f"Failed {filename}: {e}"
        )

# ==========================================
# SAVE OCR OUTPUT
# ==========================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        all_pages,
        f,
        ensure_ascii=False,
        indent=2
    )

print(
    f"\nStored {len(all_pages)} pages"
)