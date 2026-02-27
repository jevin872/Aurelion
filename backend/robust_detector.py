import numpy as np

class RobustVoiceDetector:
    """
    Compares test audio features against a baseline signature.
    Focuses strongly on detecting AI versus Human voices and same vs different speaker.
    """
    def __init__(self):
        self.baseline = None
        # Thresholds (Lower is stricter)
        self.levels = {
            "strict": 0.15,
            "normal": 0.30,
            "relaxed": 0.50,
            "very_relaxed": 0.70
        }
        # Weights
        self.weights = {
            "mfcc": 0.45,
            "phase": 0.30,
            "spectral": 0.25,
            "jitter": 0.00
        }

    def set_baseline(self, baseline_features):
        self.baseline = baseline_features

    def _calc_similarity(self, v1, v2):
        """Helper to calculate similarity between vectors/scalars"""
        v1 = np.array(v1)
        v2 = np.array(v2)
        
        # Max out at small number to prevent divide by zero
        diff = np.abs(v1 - v2)
        max_val = np.maximum(np.abs(v1), np.abs(v2))
        max_val = np.where(max_val == 0, 1e-10, max_val)
        
        variation = diff / max_val
        return float(1.0 - np.mean(variation))

    def analyze(self, test_features, strictness="normal"):
        if not self.baseline:
            return {"error": "Baseline not set"}

        # 1. MFCC Deviation (Speaker Identity)
        mfcc_sim = self._calc_similarity(self.baseline.get("mfcc_mean", []), test_features.get("mfcc_mean", []))
        mfcc_dev = max(0.0, 1.0 - mfcc_sim)
        
        # 2. Spectral Deviation (Voice Characteristics)
        spec_base = self.baseline.get("spectral_centroid_mean", 0)
        spec_test = test_features.get("spectral_centroid_mean", 0)
        spec_diff = abs(spec_test - spec_base) / max(spec_base, 1e-10)
        # Lenient scaling for spectral (from analysis doc)
        spec_dev = min(1.0, spec_diff / 0.60)
        spec_sim = 1.0 - spec_diff

        # 3. Phase Continuity Deviation (AI vs Human)
        phase_base = self.baseline.get("phase_discontinuity_mean", 0)
        phase_test = test_features.get("phase_discontinuity_mean", 0)
        phase_diff = abs(phase_test - phase_base)
        # Lenient scaling (from analysis doc)
        phase_dev = min(1.0, phase_diff / 1.0)
        phase_sim = self._calc_similarity(phase_base, phase_test)

        # Total Deviation
        weighted_deviation = (
            (mfcc_dev * self.weights["mfcc"]) +
            (phase_dev * self.weights["phase"]) +
            (spec_dev * self.weights["spectral"])
        )

        threshold = self.levels.get(strictness, self.levels["normal"])
        
        # -----------------------------------
        # Rules and Verdicts
        # -----------------------------------
        
        is_match = False
        is_ai_generated = False
        confidence = max(0.0, 1.0 - weighted_deviation)
        risk_level = "LOW"
        verdict = "Processing"
        
        # Base logical checks
        if phase_test > 2.15: # AI Generation Threshold from params
            if phase_test > 4.3 or mfcc_sim < 0.70:
                is_ai_generated = True
                is_match = False
                risk_level = "HIGH"
                verdict = "AI GENERATED VOICE DETECTED"
                confidence = min(0.99, (phase_test - 2.15) / 2.0) # High confidence if very anomalous
                
        if not is_ai_generated:
            # Did they supply the exact same file?
            if phase_sim > 0.95 and spec_sim > 0.95:
                is_match = True
                confidence = 0.98
                verdict = "Identical Features (Same Recording)"
                risk_level = "MINIMAL"
                
            # Dual check for strong match
            elif mfcc_sim > 0.90 and spec_diff < 0.10:
                is_match = True
                verdict = "Strong Match"
                risk_level = "MINIMAL"
                
            # Standard Deviation check
            elif weighted_deviation < threshold:
                is_match = True
                verdict = "Voice Matches Signature"
                risk_level = "LOW"
                
            # Missed the cut
            else:
                is_match = False
                verdict = "Mismatch / Different Speaker"
                risk_level = "MEDIUM"
                
        return {
            "is_match": is_match,
            "is_ai_generated": is_ai_generated,
            "confidence": float(confidence),
            "deviation": float(weighted_deviation),
            "threshold": threshold,
            "threshold_level": strictness,
            "risk_level": risk_level,
            "verdict": verdict,
            "mfcc_similarity": mfcc_sim,
            "phase_similarity": phase_sim,
            "spectral_similarity": spec_sim
        }
