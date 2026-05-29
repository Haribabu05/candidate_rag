# ==========================================
# FILE: backend/extract_pipeline_paddle.py
# ==========================================

import os
import json

from pdf2image import convert_from_path
from paddleocr import PaddleOCR

# ==========================================
# CONFIG
# ==========================================

PDF_FOLDER = r"data\KOLATHUR"

OUTPUT_JSON = "extracted_pages_paddle.json"

POPPLER_PATH = r"C:\poppler\Library\bin"

# ==========================================
# OCR
# ==========================================

ocr = PaddleOCR(
    use_angle_cls=False,
    lang="en"
)

# ==========================================
# STORAGE
# ==========================================

all_pages = []

# ==========================================
# LOOP PDFs
# ==========================================

pdf_files = [

 
    f for f in os.listdir(PDF_FOLDER)

    if f.lower().endswith(".pdf")
]

for pdf_file in pdf_files:

    print(
        f"Processing {pdf_file}"
    )

    pdf_path = os.path.join(
        PDF_FOLDER,
        pdf_file
    )

    # ======================================
    # PARSE FILENAME
    # ======================================

    filename = pdf_file.replace(
        ".pdf",
        ""
    )

    parts = filename.split("-")

    candidate = parts[0] if len(parts) > 0 else "Unknown"

    party = parts[1] if len(parts) > 1 else "Unknown"

    constituency = "KOLATHUR"

    # ======================================
    # PDF -> IMAGES
    # ======================================

    images = convert_from_path(

        pdf_path,

        dpi=300,

        poppler_path=POPPLER_PATH
    )

    # ======================================
    # PAGE OCR
    # ======================================

    for page_num, image in enumerate(
        images,
        start=1
    ):

        temp_file = (
            f"temp_page_{page_num}.jpg"
        )

        image.save(
            temp_file
        )

        result = ocr.ocr(
            temp_file,
            cls=False
        )

        page_text = ""

        if result and result[0]:

            for line in result[0]:

                try:

                    text = line[1][0]

                    page_text += (
                        text + "\n"
                    )

                except:
                    pass

        page_data = {

            "text": page_text,

            "metadata": {

                "candidate": candidate,

                "party": party,

                "constituency": constituency,

                "page": page_num,

                "source_file": pdf_file
            }
        }

        all_pages.append(
            page_data
        )

        os.remove(
            temp_file
        )

    print(
        f"✓ {pdf_file}"
    )

# ==========================================
# SAVE
# ==========================================

with open(

    OUTPUT_JSON,

    "w",

    encoding="utf-8"
) as f:

    json.dump(

        all_pages,

        f,

        ensure_ascii=False,

        indent=2
    )

# ==========================================
# DONE
# ==========================================

print()

print(
    f"Stored {len(all_pages)} pages"
)