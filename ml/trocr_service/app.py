# trocr_service/app.py — TrOCR handwriting recognition microservice.
# Phase 0: returns mock OCR text after a simulated delay.
# Phase 3: replace mock_extract() with real microsoft/trocr-base-handwritten inference.

from fastapi import FastAPI, UploadFile, File
import asyncio

app = FastAPI(title="TrOCR Service", version="0.1.0")


async def mock_extract(image_bytes: bytes) -> dict:
    """Simulate OCR extraction. Returns raw text + confidence score."""
    await asyncio.sleep(2)
    return {
        "text": "1. A\n2. B\n3. C\n4. D\n5. A",
        "confidence": 0.91,       # average character confidence (0–1)
        "sections": {
            "mcq": "1. A\n2. B\n3. C\n4. D\n5. A",
            "numerical": "",
            "subjective": "",
        },
    }


@app.post("/trocr/extract")
async def extract(file: UploadFile = File(...)):
    image_bytes = await file.read()
    result = await mock_extract(image_bytes)
    return result
