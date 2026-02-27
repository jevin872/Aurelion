from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import soundfile as sf
import io
import tempfile
import os
import sys
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.realtime_detector import RealtimeVoiceDetector
from backend.robust_detector import RobustVoiceDetector

app = FastAPI(title="Polyglot Ghost Voice Auth API")

# CORS configuration for Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your Vercel domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global detector instances
detector = RealtimeVoiceDetector()
robust_detector = RobustVoiceDetector()
baseline_features = None

class AnalysisRequest(BaseModel):
    strictness: str = "normal"

@app.get("/")
def read_root():
    return {
        "message": "Polyglot Ghost Voice Authentication API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/set-baseline")
async def set_baseline(file: UploadFile = File(...)):
    """Set the baseline voice signature"""
    global baseline_features
    
    try:
        # Read uploaded file
        contents = await file.read()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        # Extract features
        success = detector.set_baseline(tmp_path)
        
        # Cleanup
        os.unlink(tmp_path)
        
        if success:
            baseline_features = detector.baseline_features
            robust_detector.set_baseline(baseline_features)
            return {
                "success": True,
                "message": "Baseline signature established successfully"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to extract features. Audio might be corrupted or too silent."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_voice(
    file: UploadFile = File(...),
    strictness: str = "normal"
):
    """Analyze a voice sample against the baseline"""
    global baseline_features
    
    if baseline_features is None:
        raise HTTPException(
            status_code=400,
            detail="Baseline not set. Please set a baseline signature first."
        )
    
    try:
        # Read uploaded file
        contents = await file.read()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        # Load audio
        y, sr = sf.read(tmp_path)
        if len(y.shape) > 1:
            y = y.mean(axis=1)  # Convert to mono
        
        # Analyze
        result = detector.analyze_chunk(y, sr)
        
        # Cleanup
        os.unlink(tmp_path)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Get robust analysis
        features = result["features"]
        robust_res = robust_detector.analyze(features, strictness=strictness)
        
        return {
            "success": True,
            "is_match": robust_res["is_match"],
            "is_ai_generated": robust_res["is_ai_generated"],
            "confidence": float(robust_res["confidence"]),
            "deviation": float(robust_res["deviation"]),
            "threshold": robust_res["threshold"],
            "threshold_level": robust_res["threshold_level"],
            "risk_level": robust_res["risk_level"],
            "verdict": robust_res["verdict"],
            "mfcc_similarity": float(robust_res["mfcc_similarity"]),
            "phase_similarity": float(robust_res["phase_similarity"]),
            "spectral_similarity": float(robust_res["spectral_similarity"])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reset")
def reset_baseline():
    """Reset the baseline signature"""
    global baseline_features
    baseline_features = None
    return {"success": True, "message": "Baseline reset successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
