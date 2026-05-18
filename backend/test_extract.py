import fitz

pdf_path = r"data/MKStalin-DMK-1.pdf"

doc = fitz.open(pdf_path)

for i, page in enumerate(doc):
    text = page.get_text().strip()
    images = page.get_images()

    print(f"Page {i+1}: {len(text)} chars text | {len(images)} images")