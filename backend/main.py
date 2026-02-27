from fastapi import FastAPI, UploadFile, File
from backend.utils import analyze_voice_liveness
import shutil
import os

app = FastAPI()


@app.post("/analyze-voice")
async def analyze_voice(file: UploadFile = File(...)):
    # Save the file temporarily
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Perform analysis
    features = analyze_voice_liveness(file_path)

    # --- ROBUST THRESHOLDING ---
    # Phase inconsistency is much higher in AI.
    # Jitter is higher in sick humans, lower in AI.

    is_fake = False
    # Thresholds need tuning based on ASVspoof data
    if features["phase_inconsistency"] > 0.02 or features["jitter"] < 0.005:
        is_fake = True

    # Cleanup temp file
    os.remove(file_path)

    return {"status": "success", "features": features, "is_fake": is_fake}
