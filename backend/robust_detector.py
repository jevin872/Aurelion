"""
Robust voice detector that works even when the person is sick.
Focuses on stable biometric features that don't change with illness.
"""

import numpy as np
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RobustVoiceDetector:
    """
    Enhanced detector that's robust to voice changes from illness.
    
    Key improvements:
    1. Focus on MFCC patterns (speaker identity) over spectral features
    2. Ignore jitter and pitch variations (affected by illness)
    3. Use phase continuity for AI detection only
    4. Adaptive thresholds based on feature stability
    """
    
    def __init__(self, classifier_path='classifier_params.json'):
        self.classifier = self._load_classifier(classifier_path)
        self.baseline_features = None
        
        # --- BALANCED FEATURE WEIGHTS ---
        # Adjusted to better distinguish different speakers
        # MFCC alone is not enough - need spectral differences too
        self.feature_weights = {
            'mfcc': 0.45,           # Reduced from 60% - still important but not dominant
            'phase': 0.30,          # AI detection - significant weight
            'spectral': 0.25,       # Increased from 5% - important for speaker distinction
            'jitter': 0.00          # Ignore - too variable
        }
        
        # --- LENIENT THRESHOLDS FOR SAME-VOICE MATCHING ---
        # These thresholds account for natural voice variation
        # (recording conditions, health, time of day, etc.)
        self.deviation_thresholds = {
            'strict': 0.25,         # 25% deviation allowed
            'normal': 0.45,         # 45% deviation allowed (default - lenient)
            'relaxed': 0.65,        # 65% deviation allowed
            'very_relaxed': 0.80    # 80% deviation allowed
        }
        
        self.current_threshold = 'normal'  # Default to normal for balanced matching
        
        logger.info("RobustVoiceDetector initialized with illness tolerance")
    
    def _load_classifier(self, path):
        """Load classifier parameters."""
        if Path(path).exists():
            with open(path, 'r') as f:
                return json.load(f)
        return {
            'type': 'threshold',
            'feature': 'phase_discontinuity_mean',
            'threshold': 2.0,
        }
    
    def set_baseline(self, features):
        """Set baseline features from authentic voice."""
        self.baseline_features = features
        logger.info("Baseline features set")
    
    def set_tolerance(self, level='relaxed'):
        """
        Set tolerance level for voice matching.
        
        Args:
            level: 'strict', 'normal', 'relaxed', or 'very_relaxed'
        """
        if level in self.deviation_thresholds:
            self.current_threshold = level
            logger.info(f"Tolerance set to: {level} ({self.deviation_thresholds[level]:.0%})")
        else:
            logger.warning(f"Unknown tolerance level: {level}")
    
    def calculate_weighted_deviation(self, test_features):
        """
        Calculate weighted deviation focusing on stable features.
        
        Returns:
            float: Weighted deviation score (0-1)
        """
        if not self.baseline_features:
            return None
        
        deviations = {}
        
        # 1. MFCC deviation (most important - speaker identity)
        mfcc_baseline = np.array(self.baseline_features.get('mfcc_mean', []))
        mfcc_test = np.array(test_features.get('mfcc_mean', []))
        
        logger.info(f"MFCC arrays: baseline length={len(mfcc_baseline)}, test length={len(mfcc_test)}")
        
        if len(mfcc_baseline) > 0 and len(mfcc_test) > 0:
            # Use cosine similarity for MFCC (more robust)
            mfcc_similarity = np.dot(mfcc_baseline, mfcc_test) / (
                np.linalg.norm(mfcc_baseline) * np.linalg.norm(mfcc_test) + 1e-10
            )
            # Convert to deviation: similarity 0.95 = 0.05 deviation, 0.80 = 0.20 deviation
            mfcc_deviation = 1 - mfcc_similarity
            deviations['mfcc'] = max(0, min(1, mfcc_deviation))
            
            logger.info(f"MFCC similarity: {mfcc_similarity:.4f}, deviation: {mfcc_deviation:.4f}")
        else:
            logger.warning(f"MFCC arrays empty or mismatched! Using default deviation 0.5")
            deviations['mfcc'] = 0.5
        
        # 2. Phase continuity (AI detection)
        phase_baseline = self.baseline_features.get('phase_discontinuity_mean', 0)
        phase_test = test_features.get('phase_discontinuity_mean', 0)
        
        if phase_baseline > 0:
            # Use absolute difference with very lenient scaling
            phase_diff = abs(phase_test - phase_baseline)
            # Normalize: differences < 1.0 are considered normal for same voice
            # 0.5 diff = 0.5 deviation, 1.0 diff = 1.0 deviation
            phase_deviation = min(1, phase_diff / 1.0)
            deviations['phase'] = phase_deviation
            
            logger.info(f"Phase: baseline={phase_baseline:.4f}, test={phase_test:.4f}, diff={phase_diff:.4f}, deviation={phase_deviation:.3f}")
        else:
            deviations['phase'] = 0
        
        # 3. Spectral features (less weight - affected by illness)
        spectral_features = ['spectral_centroid_mean']
        spectral_deviations = []
        
        for feature in spectral_features:
            baseline_val = self.baseline_features.get(feature, 0)
            test_val = test_features.get(feature, 0)
            
            if baseline_val > 0:
                # Use percentage difference with very lenient tolerance
                # Spectral centroid can vary ±30% for same voice (recording conditions, health, etc.)
                percent_diff = abs(test_val - baseline_val) / baseline_val
                # Scale: 30% diff = 0.5 deviation, 60% diff = 1.0 deviation
                dev = min(1, percent_diff / 0.60)
                spectral_deviations.append(dev)
                
                logger.info(f"Spectral: baseline={baseline_val:.2f}, test={test_val:.2f}, diff={percent_diff:.1%}, deviation={dev:.3f}")
        
        if spectral_deviations:
            deviations['spectral'] = np.mean(spectral_deviations)
        else:
            deviations['spectral'] = 0
        
        # 4. Jitter (minimal weight but check for extreme differences)
        jitter_baseline = self.baseline_features.get('jitter', 0)
        jitter_test = test_features.get('jitter', 0)
        
        if jitter_baseline > 0:
            # Jitter can vary ±50% for same voice (affected by recording conditions)
            jitter_diff_percent = abs(jitter_test - jitter_baseline) / jitter_baseline
            # Scale: 50% diff = 0.5 deviation, 100% diff = 1.0 deviation
            deviations['jitter'] = min(1, jitter_diff_percent / 1.0)
            
            logger.info(f"Jitter: baseline={jitter_baseline:.6f}, test={jitter_test:.6f}, diff={jitter_diff_percent:.1%}, deviation={deviations['jitter']:.3f}")
        else:
            deviations['jitter'] = 0
        
        # Calculate weighted average
        weighted_deviation = sum(
            deviations[key] * self.feature_weights[key]
            for key in deviations
        )
        
        logger.info(f"Feature deviations: MFCC={deviations.get('mfcc', 0):.3f}, Phase={deviations.get('phase', 0):.3f}, Spectral={deviations.get('spectral', 0):.3f}, Jitter={deviations.get('jitter', 0):.3f}")
        logger.info(f"Weighted deviation: {weighted_deviation:.3f}")
        
        return weighted_deviation
    
    def analyze(self, test_features):
        """
        Analyze test features against baseline.
        
        Returns:
            dict: Analysis results with match status and confidence
        """
        if not self.baseline_features:
            return {
                'error': 'No baseline set',
                'is_match': False,
                'confidence': 0
            }
        
        # Calculate weighted deviation
        deviation = self.calculate_weighted_deviation(test_features)
        
        # Get current threshold
        threshold = self.deviation_thresholds[self.current_threshold]
        
        # SPECIAL CASE 1: Check if individual features are nearly identical
        # This catches cases where the same audio is being compared
        phase_baseline = self.baseline_features.get('phase_discontinuity_mean', 0)
        phase_test = test_features.get('phase_discontinuity_mean', 0)
        spectral_baseline = self.baseline_features.get('spectral_centroid_mean', 0)
        spectral_test = test_features.get('spectral_centroid_mean', 0)
        
        # Calculate individual feature similarities
        phase_similarity = 1 - (abs(phase_test - phase_baseline) / max(phase_baseline, 0.01))
        spectral_similarity = 1 - (abs(spectral_test - spectral_baseline) / max(spectral_baseline, 1))
        
        # If both phase and spectral are >95% similar, it's the same voice
        nearly_identical = (phase_similarity > 0.95 and spectral_similarity > 0.95)
        
        logger.info(f"Nearly identical check: phase_sim={phase_similarity:.3f}, spectral_sim={spectral_similarity:.3f}, nearly_identical={nearly_identical}")
        
        # SPECIAL CASE 2: Check MFCC similarity directly for same-voice detection
        # If MFCC similarity is very high (>0.80), it's likely the same person
        mfcc_baseline = np.array(self.baseline_features.get('mfcc_mean', []))
        mfcc_test = np.array(test_features.get('mfcc_mean', []))
        
        mfcc_similarity = 0
        if len(mfcc_baseline) > 0 and len(mfcc_test) > 0:
            mfcc_similarity = np.dot(mfcc_baseline, mfcc_test) / (
                np.linalg.norm(mfcc_baseline) * np.linalg.norm(mfcc_test) + 1e-10
            )
        
        # If MFCC similarity is very high, override other checks
        # BUT: Also check spectral similarity to avoid false matches
        high_mfcc_match = mfcc_similarity > 0.90  # Increased threshold from 0.80 to 0.90
        
        # Additional check: spectral features should also be similar for same speaker
        spectral_baseline = self.baseline_features.get('spectral_centroid_mean', 0)
        spectral_test = test_features.get('spectral_centroid_mean', 0)
        spectral_diff_percent = abs(spectral_test - spectral_baseline) / max(spectral_baseline, 1)
        spectral_similar = spectral_diff_percent < 0.30  # Within 30% (more lenient)
        
        # High MFCC match only counts if spectral is also similar
        high_mfcc_match = high_mfcc_match and spectral_similar
        
        logger.info(f"High MFCC match check: mfcc_sim={mfcc_similarity:.3f}, spectral_diff={spectral_diff_percent:.1%}, spectral_similar={spectral_similar}, high_mfcc_match={high_mfcc_match}")
        
        # Determine match (with special cases)
        is_match = deviation < threshold or high_mfcc_match or nearly_identical
        
        # Calculate confidence (inverse of deviation, scaled)
        if is_match:
            # For matches, confidence increases as deviation decreases
            if nearly_identical:
                # Nearly identical features = very high confidence
                confidence = 0.98
            elif high_mfcc_match:
                # High MFCC match = high confidence
                confidence = max(0.85, mfcc_similarity)
            else:
                confidence = 1 - (deviation / threshold)
        else:
            # For mismatches, confidence increases as deviation increases
            confidence = min(1, (deviation - threshold) / (1 - threshold))
        
        # Check for AI-generated voice (high phase discontinuity)
        # BUT: Only flag as AI if MFCC similarity is LOW (different speaker)
        # Increased threshold to reduce false positives on borderline cases
        phase_threshold = self.classifier.get('threshold', 2.0)
        phase_value = test_features.get('phase_discontinuity_mean', 0)
        
        # Use a higher multiplier (2.0x) to only catch clear AI cases
        # This prevents borderline values from being flagged
        is_ai_generated = (phase_value > phase_threshold * 2.0) and (mfcc_similarity < 0.70)
        
        # Determine risk level
        if is_ai_generated:
            risk_level = 'HIGH'
        elif deviation > threshold * 1.5 and not high_mfcc_match:
            risk_level = 'HIGH'
        elif deviation > threshold * 1.2:
            risk_level = 'MEDIUM'
        elif deviation > threshold * 0.8:
            risk_level = 'LOW'
        else:
            risk_level = 'MINIMAL'
        
        # Generate verdict
        if is_ai_generated:
            verdict = "AI-GENERATED VOICE DETECTED"
        elif not is_match:
            verdict = "VOICE MISMATCH - Different Speaker"
        else:
            if nearly_identical:
                verdict = "VOICE MATCH - Identical Features (Same Recording)"
            elif high_mfcc_match:
                verdict = "VOICE MATCH - Same Speaker (High MFCC Similarity)"
            elif confidence > 0.8:
                verdict = "VOICE MATCH - High Confidence"
            elif confidence > 0.6:
                verdict = "VOICE MATCH - Medium Confidence"
            else:
                verdict = "VOICE MATCH - Low Confidence (May be sick/tired)"
        
        return {
            'is_match': is_match,
            'is_ai_generated': is_ai_generated,
            'confidence': float(confidence),
            'deviation': float(deviation),
            'threshold': float(threshold),
            'threshold_level': self.current_threshold,
            'risk_level': risk_level,
            'verdict': verdict,
            'mfcc_similarity': float(mfcc_similarity),
            'high_mfcc_match': high_mfcc_match,
            'nearly_identical': nearly_identical,
            'phase_similarity': float(phase_similarity) if phase_similarity else 0,
            'spectral_similarity': float(spectral_similarity) if spectral_similarity else 0,
            'feature_breakdown': {
                'mfcc_weight': self.feature_weights['mfcc'],
                'phase_weight': self.feature_weights['phase'],
                'spectral_weight': self.feature_weights['spectral'],
                'jitter_weight': self.feature_weights['jitter']
            }
        }


def create_robust_detector():
    """Factory function to create a robust detector."""
    return RobustVoiceDetector()


if __name__ == "__main__":
    # Test the robust detector
    detector = RobustVoiceDetector()
    
    print("=" * 80)
    print("ROBUST VOICE DETECTOR - ILLNESS TOLERANT")
    print("=" * 80)
    
    print("\nFeature Weights:")
    for feature, weight in detector.feature_weights.items():
        print(f"  {feature}: {weight:.0%}")
    
    print("\nDeviation Thresholds:")
    for level, threshold in detector.deviation_thresholds.items():
        marker = " ← Current" if level == detector.current_threshold else ""
        print(f"  {level}: {threshold:.0%}{marker}")
    
    print("\n" + "=" * 80)
    print("Key Features:")
    print("  • Focuses on MFCC (60%) - stable speaker identity")
    print("  • Ignores jitter (0%) - varies when sick")
    print("  • Reduced spectral weight (15%) - affected by illness")
    print("  • Uses phase (25%) for AI detection only")
    print("  • Default threshold: 50% (relaxed for illness)")
    print("=" * 80)
