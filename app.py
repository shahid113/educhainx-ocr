import io
import pytesseract
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pdf2image import convert_from_bytes
from PIL import Image, ImageEnhance, ImageFilter

from gemini_processor import extract_certificate_json

app = FastAPI(
    title="OCR + Gemini API",
    version="1.0"
)

def preprocess(img: Image.Image) -> Image.Image:
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(2)
    img = img.filter(ImageFilter.SHARPEN)

    w, h = img.size
    if w < 1000:
        scale = 1000 / w
        img = img.resize((int(w * scale), int(h * scale)))

    return img


@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    filename = file.filename.lower()
    data = await file.read()

    try:
        # PDF → first page only
        if filename.endswith(".pdf"):
            pages = convert_from_bytes(data)
            if not pages:
                raise HTTPException(status_code=400, detail="PDF has no pages")
            image = pages[0]
        else:
            image = Image.open(io.BytesIO(data)).convert("RGB")

        processed = preprocess(image)

        text = pytesseract.image_to_string(
            processed,
            config="--oem 3 --psm 6"
        ).strip()

        # Send to Gemini for clean JSON extraction
        gemini_json = extract_certificate_json(text)

        return JSONResponse({"certificateData": gemini_json})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
