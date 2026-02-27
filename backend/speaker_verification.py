"""
Speaker Verification System using MFCC
Verifies if a test voice matches the authenticated user's signature.
"""

import numpy as np
from scipy.spatial.distance import cosine, euclidean
from sklearn.metrics.pairwise import cosine_similarity
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpeakerVerifier:
    """
    MFCC-based speaker verification system.
    Uses cosine similarity and Euclidean distance for matching.
    """
    
    def __init__(self, threshold=0.85):
        """
        Initialize speaker verifier.
        
        Args:
            threshold: Cosine similarity threshold for accepting a match (0-1)
                      Higher = stricter matching
        """
        self.threshold = threshold
        self.signature_mfcc = None
        self.signature_stats = None
        
        logger.info(f"SpeakerVerifier initialized with threshold={threshold}")
    
    def enroll_speaker(self, mfcc_features):
        """
        Enroll a speaker by storing their MFCC signature.
        
        Args:
            mfcc_features: Dictionary containing 'mfcc_mean', 'mfcc_std', 'mfcc_delta_mean'
        
        Returns:
            bool: Success status
        """
        try:
            mfcc_mean = np.array(mfcc_features.get('mfcc_mean', []))
            mfcc_std = np.array(mfcc_features.get('mfcc_std', []))
            mfcc_delta = np.array(mfcc_features.get('mfcc_delta_mean', []))
            
            if len(mfcc_mean) == 0:
                logger.error("MFCC features are empty")
                return False
            
            # Store signature
            self.signature_mfcc = {
                'mean': mfcc_mean,
                'std': mfcc_std,
                'delta': mfcc_delta
            }
            
            # Calculate statistics for normalization
            self.signature_stats = {
                'mean_norm': np.linalg.norm(mfcc_mean),
                'std_norm': np.linalg.norm(mfcc_std),
                'delta_norm': np.linalg.norm(mfcc_delta)
            }
            
            logger.info(f"Speaker enrolled successfully. MFCC dimensions: {len(mfcc_mean)}")
            return True
            
        except Exception as e:
            logger.error(f"Error enrolling speaker: {e}")
            return False
    
    def verify_speaker(self, test_mfcc_features):
        """
        Verify if test voice matches enrolled speaker.
        
        Args:
            test_mfcc_features: Dictionary containing MFCC features
        
        Returns:
            dict: Verification results with scores and decision
        """
        if self.signature_mfcc is None:
            return {
                'error': 'No speaker enrolled',
                'is_match': False,
                'score': 0.0
            }
        
        try:
            # Extract test features
            test_mean = np.array(test_mfcc_features.get('mfcc_mean', []))
            test_std = np.array(test_mfcc_features.get('mfcc_std', []))
            test_delta = np.array(test_mfcc_features.get('mfcc_delta_mean', []))
            
            if len(test_mean) == 0:
                return {
                    'error': 'Test MFCC features are empty',
                    'is_match': False,
                    'score': 0.0
                }
            
            # Calculate cosine similarity for each component
            cosine_mean = self._cosine_similarity(self.signature_mfcc['mean'], test_mean)
            cosine_std = self._cosine_similarity(self.signature_mfcc['std'], test_std)
            cosine_delta = self._cosine_similarity(self.signature_mfcc['delta'], test_delta)
            
            # Calculate Euclidean distance (normalized)
            euclidean_mean = self._normalized_euclidean(
                self.signature_mfcc['mean'], 
                test_mean,
                self.signature_stats['mean_norm']
            )
            
            # Weighted combination (cosine similarity is primary)
            # Mean MFCC is most important, delta second, std third
            weights = {'mean': 0.60, 'std': 0.15, 'delta': 0.25}
            
            combined_score = (
                cosine_mean * weights['mean'] +
                cosine_std * weights['std'] +
                cosine_delta * weights['delta']
            )
            
            # Decision
            is_match = combined_score >= self.threshold
            
            # Confidence (how far from threshold)
            confidence = abs(combined_score - self.threshold) / (1 - self.threshold) if not is_match else (combined_score - self.threshold) / (1 - self.threshold)
            confidence = min(1.0, max(0.0, confidence))
            
            result = {
                'is_match': bool(is_match),
                'score': float(combined_score),
                'threshold': float(self.threshold),
                'confidence': float(confidence),
                'details': {
                    'cosine_mean': float(cosine_mean),
                    'cosine_std': float(cosine_std),
                    'cosine_delta': float(cosine_delta),
                    'euclidean_distance': float(euclidean_mean),
                    'weights': weights
                }
            }
            
            logger.info(f"Verification: score={combined_score:.4f}, threshold={self.threshold:.4f}, match={is_match}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error verifying speaker: {e}")
            return {
                'error': str(e),
                'is_match': False,
                'score': 0.0
            }
    
    def _cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            logger.warning(f"Vector length mismatch: {len(vec1)} vs {len(vec2)}")
            return 0.0
        
        # Cosine similarity: 1 - cosine distance
        similarity = 1 - cosine(vec1, vec2)
        return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]
    
    def _normalized_euclidean(self, vec1, vec2, norm_factor):
        """Calculate normalized Euclidean distance."""
        if len(vec1) != len(vec2):
            return 1.0
        
        distance = euclidean(vec1, vec2)
        normalized = distance / (norm_factor + 1e-10)
        return min(1.0, normalized)
    
    def set_threshold(self, threshold):
        """Update verification threshold."""
        self.threshold = max(0.0, min(1.0, threshold))
        logger.info(f"Threshold updated to {self.threshold}")


def calculate_eer(genuine_scores, impostor_scores):
    """
    Calculate Equal Error Rate (EER) from genuine and impostor scores.
    
    Args:
        genuine_scores: List of similarity scores for genuine (same speaker) pairs
        impostor_scores: List of similarity scores for impostor (different speaker) pairs
    
    Returns:
        dict: EER and related metrics
    """
    # Combine scores with labels
    scores = np.concatenate([genuine_scores, impostor_scores])
    labels = np.concatenate([
        np.ones(len(genuine_scores)),   # 1 = genuine
        np.zeros(len(impostor_scores))  # 0 = impostor
    ])
    
    # Sort by score
    sorted_indices = np.argsort(scores)
    sorted_scores = scores[sorted_indices]
    sorted_labels = labels[sorted_indices]
    
    # Calculate FAR and FRR for different thresholds
    thresholds = sorted_scores
    far_list = []
    frr_list = []
    
    for threshold in thresholds:
        # False Accept Rate: impostors accepted (score >= threshold)
        impostor_accepted = np.sum((scores >= threshold) & (labels == 0))
        far = impostor_accepted / len(impostor_scores) if len(impostor_scores) > 0 else 0
        
        # False Reject Rate: genuines rejected (score < threshold)
        genuine_rejected = np.sum((scores < threshold) & (labels == 1))
        frr = genuine_rejected / len(genuine_scores) if len(genuine_scores) > 0 else 0
        
        far_list.append(far)
        frr_list.append(frr)
    
    far_array = np.array(far_list)
    frr_array = np.array(frr_list)
    
    # Find EER (where FAR = FRR)
    diff = np.abs(far_array - frr_array)
    eer_index = np.argmin(diff)
    eer = (far_array[eer_index] + frr_array[eer_index]) / 2
    eer_threshold = thresholds[eer_index]
    
    return {
        'eer': float(eer),
        'eer_threshold': float(eer_threshold),
        'far_at_eer': float(far_array[eer_index]),
        'frr_at_eer': float(frr_array[eer_index]),
        'thresholds': thresholds.tolist(),
        'far': far_array.tolist(),
        'frr': frr_array.tolist()
    }


def calculate_accuracy_metrics(genuine_scores, impostor_scores, threshold):
    """
    Calculate accuracy metrics at a given threshold.
    
    Args:
        genuine_scores: Scores for genuine pairs
        impostor_scores: Scores for impostor pairs
        threshold: Decision threshold
    
    Returns:
        dict: Accuracy metrics
    """
    # True Positives: genuine pairs accepted
    tp = np.sum(np.array(genuine_scores) >= threshold)
    
    # False Negatives: genuine pairs rejected
    fn = np.sum(np.array(genuine_scores) < threshold)
    
    # True Negatives: impostor pairs rejected
    tn = np.sum(np.array(impostor_scores) < threshold)
    
    # False Positives: impostor pairs accepted
    fp = np.sum(np.array(impostor_scores) >= threshold)
    
    # Calculate metrics
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    far = fp / (fp + tn) if (fp + tn) > 0 else 0
    frr = fn / (fn + tp) if (fn + tp) > 0 else 0
    
    return {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1_score),
        'far': float(far),
        'frr': float(frr),
        'true_positives': int(tp),
        'false_positives': int(fp),
        'true_negatives': int(tn),
        'false_negatives': int(fn)
    }


if __name__ == "__main__":
    # Example usage
    print("=" * 80)
    print("SPEAKER VERIFICATION SYSTEM - MFCC Based")
    print("=" * 80)
    
    # Create verifier
    verifier = SpeakerVerifier(threshold=0.85)
    
    print("\nFeatures:")
    print("  - MFCC-based speaker verification")
    print("  - Cosine similarity matching")
    print("  - Configurable threshold")
    print("  - EER calculation support")
    
    print("\nUsage:")
    print("  1. Enroll speaker with MFCC features")
    print("  2. Verify test samples against enrolled speaker")
    print("  3. Calculate EER from genuine/impostor scores")
    
    print("\n" + "=" * 80)
