import os
import json
import librosa
from backend.audio_normalizer import normalize_audio
from backend.feature_extraction_fast import extract_features

class RealtimeVoiceDetector:
    """
    Handles single-file baseline extraction and real-time audio chunk extraction.
    """
    def __init__(self):
        self.baseline_features = None

    def set_baseline(self, audio_file_path):
        """
        Extracts features from an audio file to use as the signature.
        """
        features = extract_features(audio_file_path)
        if features:
            self.baseline_features = features
            return True
        return False

    def analyze_chunk(self, y, sr):
        """
        Analyzes a chunk of audio against the set baseline.
        """
        if self.baseline_features is None:
            return {"error": "Baseline not set"}

        # Normalize audio chunk
        y_norm, norm_sr = normalize_audio(y, sr, target_duration=3.5)
        
        # Save temp file to reuse existing extraction flow
        temp_file = "temp_chunk.wav"
        import soundfile as sf
        sf.write(temp_file, y_norm, norm_sr)
        
        # Extract features
        features = extract_features(temp_file)
        
        if os.path.exists(temp_file):
            os.remove(temp_file)

        if not features:
            return {"error": "Failed to extract features from test audio"}

        return {
            "success": True,
            "features": features
        }
