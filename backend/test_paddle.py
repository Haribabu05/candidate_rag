# ==========================================
# FILE: backend/test_paddle.py
# ==========================================

from paddleocr import PaddleOCR
from pdf2image import convert_from_path

# ==========================================
# POPPLER PATH
# ==========================================

POPPLER_PATH = (
    r"C:\poppler\Library\bin"
)

# ==========================================
# PDF FILE
# ==========================================

PDF_PATH = (
    r"data\KOLATHUR\MKStalin-DMK-1.pdf"
)

# ==========================================
# LOAD OCR
# ==========================================

ocr = PaddleOCR(

    use_textline_orientation=True,

    lang="en"
)

# ==========================================
# PDF TO IMAGES
# ==========================================

print(
    "\nConverting PDF pages..."
)

images = convert_from_path(

    PDF_PATH,

    dpi=300,

    poppler_path=POPPLER_PATH
)

print(
    f"Converted {len(images)} pages"
)

# ==========================================
# TEST FIRST PAGE
# ==========================================

first_page = images[0]

TEMP_IMAGE = "temp_page.jpg"

first_page.save(
    TEMP_IMAGE
)

print(
    "\nRunning PaddleOCR...\n"
)

# ==========================================
# OCR
# ==========================================

result = ocr.ocr(

    TEMP_IMAGE
)

# ==========================================
# PRINT RESULTS
# ==========================================

for line in result[0]:

    text = line[1][0]

    confidence = line[1][1]

    print(

        f"{text}"

        f"  | confidence={confidence:.2f}"
    )