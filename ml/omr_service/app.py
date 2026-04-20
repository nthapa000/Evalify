# omr_service/app.py — OMR (Optical Mark Recognition) microservice.
# Phase 0: returns mock data after a simulated delay.
# Phase 3: replace mock_detect() with real OpenCV bubble detection.

from fastapi import FastAPI, UploadFile, File
import asyncio

app = FastAPI(title="OMR Service", version="0.1.0")


async def mock_detect(image_bytes: bytes) -> dict:
    """Simulate bubble detection with a 2-second delay. Returns Q→answer map."""
    await asyncio.sleep(2)
    # Mock: 5-question MCQ, all answered "A"
    return {f"Q{i}": "A" for i in range(1, 6)}


@app.post("/omr/detect")
async def detect(file: UploadFile = File(...)):
    image_bytes = await file.read()
    answers = await mock_detect(image_bytes)
    return {"answers": answers}
