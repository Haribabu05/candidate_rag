from pdf2image import convert_from_path
from paddleocr import PaddleOCR

# Convert page 16
images = convert_from_path(
    r"test_data\MKStalin-DMK-1.pdf",
    first_page=16,
    last_page=16
)

images[0].save("page16.png")

# Tamil OCR
ocr = PaddleOCR(
    lang="ta",
    use_angle_cls=False
)

result = ocr.ocr(
    "page16.png",
    cls=False
)

# Save output
with open(
    "page16_ocr.txt",
    "w",
    encoding="utf-8"
) as f:

    for line in result[0]:

        text = line[1][0]

        f.write(text)
        f.write("\n")

print("Saved OCR output to page16_ocr.txt")