import json
import numpy as np
from pathlib import Path
from backend.dl_extractor import KuralPulseExtractor

class KuralPulseAuthEngine:
    def __init__(self, baseline_path="vocal_twin.json"):
        self.baseline_path = Path(baseline_path)
        self.baseline_profile = None
        
        # Load the baseline profile into cache if it exists
        if self.baseline_path.exists():
            try:
                with open(self.baseline_path, "r") as f:
                    self.baseline_profile = json.load(f)
            except Exception as e:
                print(f"Failed to load Vocal Twin baseline: {e}")

    def cosine_similarity(self, vec_a, vec_b):
        """Calculates cosine similarity between two biological embedding vectors."""
        vec_a_arr, vec_b_arr = np.array(vec_a), np.array(vec_b)
        
        if len(vec_a_arr) == 0 or len(vec_b_arr) == 0:
            return 0.0
            
        dot_product = np.dot(vec_a_arr, vec_b_arr)
        norm_a = np.linalg.norm(vec_a_arr)
        norm_b = np.linalg.norm(vec_b_arr)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def set_vocal_twin(self, profile):
        """Securely stores the base signature profile."""
        if not profile or not profile.get("identity_embedding"):
            return False
            
        self.baseline_profile = profile
        try:
            with open(self.baseline_path, "w") as f:
                json.dump(profile, f, indent=4)
            return True
        except Exception as e:
            print(f"Failed to save Vocal Twin: {e}")
            return False

    def is_ai_probability(self, artifacts):
        """
        Determines the AI Synthetic Probability percentage strictly utilizing Wav2Vec
        variance algorithms and deep phase discontinuities.
        """
        probability = 0.05 # Base digital signal assumption
        
        # Phase Discontinuity represents physical stitching of vocoded audio
        # Natural human speech has smooth STFT transitions (mean approx < 2.0 but > 1.2)
        # Deepfakes often peak > 2.25 due to griffin-lim or HiFi-GAN artifacts
        # Advanced fakes (like ElevenLabs) sometimes over-smooth phase < 1.0!
        phase_discontinuity = artifacts.get("phase_discontinuity_mean", 0.0)
        if phase_discontinuity > 2.15:
            probability += 0.40  # 40% strict penalty for unnatural phase jumps
        elif phase_discontinuity < 1.20 and phase_discontinuity > 0:
            probability += 0.25  # Unnaturally perfectly smooth phase (Generative diffusion)

        # Wav2Vec Latent space variance: AI clones struggle to produce natural sub-phonetic variance
        # Typically natural > 0.05, AI rigid < 0.03
        w2v_variance = artifacts.get("w2v_latent_variance", 0.1)
        if w2v_variance < 0.04:
            probability += 0.35
        elif w2v_variance < 0.06:
            probability += 0.15

        # MFCC smoothing (AI sometimes produces overly smooth resonance patterns compared to real breathy voice)
        mfcc = artifacts.get("mfcc_mean", [])
        if len(mfcc) > 0 and np.std(mfcc) < 15.0:
            probability += 0.15

        # Cap at 99% Probability for sanity
        return min(probability, 0.99)

    def verify(self, test_profile):
        """
        Multifactor Authentication Route.
        Checks Identity Match AND AI Synthetic Probability.
        """
        if not self.baseline_profile:
            return {"error": "No Vocal Twin Signature enrolled."}
            
        # 1. Identity Check (Speaker Verification)
        id_similarity = self.cosine_similarity(
            self.baseline_profile.get("identity_embedding", []),
            test_profile.get("identity_embedding", [])
        )
        
        # The typical identical-speaker threshold for SpeechBrain ECAPA-TDNN is ~0.25 (raw cosine scoring).
        # We must statistically scale the raw similarity onto the visual percentage curve.
        # Since the user requested 70% to be the new authorization cut-off, we map 0.25 directly to 70%.
        if id_similarity >= 0.25:
            # Map [0.25, 1.0] -> [70.0%, 100.0%]
            identity_match_percentage = 70.0 + ((id_similarity - 0.25) / 0.75) * 30.0
        else:
            # Map [0.0, 0.25] -> [0.0%, 70.0%] (Negative similarities map to 0%)
            identity_match_percentage = max(0.0, (id_similarity / 0.25) * 70.0)
        
        # 2. Synthetic Artifact Assessment (The Ghost Layer)
        ai_probability_ratio = self.is_ai_probability(test_profile.get("artifacts", {}))
        ai_probability_percentage = ai_probability_ratio * 100
        
        # 3. Decision Logic thresholds defined by prompt
        verdict = "AUTHORIZED"
        reason = "Matched successfully."
        passed = True
        
        # The AI Probability rule trumps identity matching
        if ai_probability_percentage >= 70.0:
            passed = False
            verdict = "DEEPFAKE ATTEMPT BLOCKED"
            reason = "High synthetic artifact probability detected. Identity match ignored."
        # If AI is low but identity doesn't match
        elif identity_match_percentage < 70.0:
            passed = False
            verdict = "UNAUTHORIZED USER DETECTED"
            reason = "Biological embedding similarity below 70% requirement."

        return {
            "passed": passed,
            "verdict": verdict,
            "reason": reason,
            "identity_match_score": identity_match_percentage,
            "ai_probability_score": ai_probability_percentage,
            "requires_liveness": 55.0 <= ai_probability_percentage < 70.0 # Trigger featherless if suspicious but not blocked immediately
        }
