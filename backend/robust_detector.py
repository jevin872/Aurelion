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
        
        # Initialize variables
        is_match = False
        is_ai_generated = False
        confidence = max(0.0, 1.0 - weighted_deviation)
        risk_level = "LOW"
        verdict = "Processing"
        
        # -----------------------------------
        # AI Detection Logic (Advanced Frequency Analysis)
        # -----------------------------------
        
        # Check multiple AI indicators based on frequency patterns
        ai_indicators = 0
        ai_reasons = []
        
        # 1. Phase discontinuity analysis (unnatural transitions)
        if phase_test < 0.3:  # Too smooth - AI voices lack natural micro-variations
            ai_indicators += 2  # Strong indicator
            ai_reasons.append("Unnaturally smooth phase transitions")
        elif phase_test > 2.5:  # Too erratic - generation artifacts
            ai_indicators += 2
            ai_reasons.append("Artificial phase artifacts detected")
        
        # 2. Spectral consistency (AI voices are too consistent)
        spec_std = test_features.get("spectral_centroid_std", 0)
        if spec_std < 80:  # Human voices naturally vary more
            ai_indicators += 1
            ai_reasons.append("Spectral variance too low (robotic)")
        
        # 3. Spectral bandwidth analysis (frequency range)
        spec_bw_mean = test_features.get("spectral_bandwidth_mean", 0)
        spec_bw_std = test_features.get("spectral_bandwidth_std", 0)
        if spec_bw_std < 100:  # AI maintains too consistent bandwidth
            ai_indicators += 1
            ai_reasons.append("Frequency bandwidth too stable")
        
        # 4. MFCC uniformity (AI produces too uniform patterns)
        mfcc_std = test_features.get("mfcc_std", [])
        if mfcc_std and np.mean(mfcc_std) < 8:  # Human speech has more variation
            ai_indicators += 1
            ai_reasons.append("Voice patterns unnaturally uniform")
        
        # 5. Zero crossing rate (frequency transitions)
        zcr = test_features.get("zero_crossing_rate_mean", 0)
        zcr_std = test_features.get("zero_crossing_rate_std", 0)
        if zcr < 0.02 or zcr > 0.4:  # Outside human range
            ai_indicators += 1
            ai_reasons.append("Abnormal frequency transitions")
        if zcr_std < 0.01:  # Too consistent
            ai_indicators += 1
            ai_reasons.append("Frequency transitions too regular")
        
        # 6. Spectral contrast (harmonic structure)
        spec_contrast_std = test_features.get("spectral_contrast_std", [])
        if spec_contrast_std and np.mean(spec_contrast_std) < 2:
            ai_indicators += 1
            ai_reasons.append("Harmonic structure too perfect")
        
        # 7. Jitter analysis (micro-variations in pitch)
        jitter = test_features.get("jitter", 0)
        if jitter < 0.001:  # AI voices lack natural jitter
            ai_indicators += 2  # Strong indicator
            ai_reasons.append("Missing natural vocal micro-variations")
        elif jitter > 0.05:  # Too much jitter (artifacts)
            ai_indicators += 1
            ai_reasons.append("Excessive pitch instability")
        
        # Detect AI if 3 or more indicators present (more strict)
        if ai_indicators >= 3:
            is_ai_generated = True
            is_match = False
            risk_level = "CRITICAL"
            verdict = f"AI GENERATED VOICE DETECTED ({', '.join(ai_reasons[:2])})"
            confidence = min(0.98, 0.6 + (ai_indicators * 0.08))
        
        # -----------------------------------
        # Identity Matching Logic
        # -----------------------------------
        
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
