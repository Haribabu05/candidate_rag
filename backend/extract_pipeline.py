import os
import json
import pytesseract

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

from pdf2image import convert_from_path

# ======================================
# CONFIG
# ======================================

PDF_FOLDER = r"data\KOLATHUR"

OUTPUT_FILE = "extracted_pages.json"

POPPLER_PATH = r"C:\poppler\Library\bin"

# ======================================
# STORAGE
# ======================================

all_pages = []

# ======================================
# PROCESS PDFs
# ======================================

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

                    "candidate": (
                        filename.split("-")[0]
                    ),

                    "party": (
                        filename.split("-")[1]
                    ),

                    "constituency": "KOLATHUR"
                }
            }

            all_pages.append(page_data)

        print(f"✓ {filename}")

    except Exception as e:

        print(
            f"Failed {filename}: {e}"
        )

# ======================================
# SAVE
# ======================================

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