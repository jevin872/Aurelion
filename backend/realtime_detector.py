"""
Real-time voice authentication engine for The Polyglot Ghost.
Processes audio streams and provides instant deepfake detection.
"""

import numpy as np
import librosa
from collections import deque
import json
from pathlib import Path
import time
from typing import Dict, Tuple, Optional
import logging

from backend.feature_extraction_fast import (
    extract_mfcc_features_fast,
    extract_stft_features_fast,
    extract_phase_continuity_features_fast
)
from backend.utils import calculate_jitter
from backend.audio_normalizer import prepare_audio_for_analysis, extract_segments

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealtimeVoiceDetector:
    """
    Real-time voice authentication detector for streaming audio.
    Analyzes audio chunks and provides instant deepfake detection.
    """
    
    def __init__(self, classifier_path='classifier_params.json', buffer_size=5):
        """
        Initialize the real-time detector.
        
        Args:
            classifier_path: Path to trained classifier parameters
            buffer_size: Number of recent predictions to keep for smoothing
        """
        self.classifier = self._load_classifier(classifier_path)
        self.buffer_size = buffer_size
        self.prediction_buffer = deque(maxlen=buffer_size)
        self.feature_history = deque(maxlen=buffer_size)
        self.baseline_features = None
        
        logger.info("RealtimeVoiceDetector initialized")
    
    def _load_classifier(self, path: str) -> Dict:
        """Load classifier parameters."""
        if Path(path).exists():
            with open(path, 'r') as f:
                return json.load(f)
        else:
            # Default classifier
            logger.warning(f"Classifier not found at {path}, using defaults")
            return {
                'type': 'threshold',
                'feature': 'phase_discontinuity_mean',
                'threshold': 1.5,
                'mean': 1.0,
                'std': 0.5
            }
    
    def set_baseline(self, audio_path: str):
        """
        Set baseline features from a known authentic voice sample.
        
        Args:
            audio_path: Path to authentic voice sample
        """
        try:
            logger.info(f"Setting baseline from {audio_path}")
            
            # Load audio
            import librosa
            y, sr = librosa.load(audio_path, sr=16000, mono=True)
            
            # Normalize audio length to 3.5 seconds
            y_normalized = prepare_audio_for_analysis(y, sr, method='best')
            
            logger.info(f"Audio normalized: {len(y)/sr:.2f}s -> {len(y_normalized)/sr:.2f}s")
            
            # Extract features from normalized audio
            mfcc = extract_mfcc_features_fast(y_normalized, sr)
            stft = extract_stft_features_fast(y_normalized, sr)
            phase = extract_phase_continuity_features_fast(y_normalized, sr)
            
            # Save temp file for jitter calculation
            import tempfile
            import soundfile as sf
            import time as time_module
            
            # Create temp file with explicit delete=False
            tmp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            tmp_path = tmp_file.name
            tmp_file.close()  # Close file handle immediately
            
            # Write audio
            sf.write(tmp_path, y_normalized, sr)
            
            # Small delay to ensure file is written
            time_module.sleep(0.1)
            
            # Calculate jitter
            jitter = calculate_jitter(tmp_path)
            
            # Clean up - try multiple times if locked
            for attempt in range(3):
                try:
                    Path(tmp_path).unlink()
                    break
                except Exception as e:
                    if attempt < 2:
                        time_module.sleep(0.2)
                    else:
                        logger.warning(f"Could not delete temp file: {e}")
            
            self.baseline_features = {
                **mfcc,
                **stft,
                **phase,
                'jitter': jitter
            }
            
            logger.info("Baseline features set successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting baseline: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def analyze_chunk(self, audio_data: np.ndarray, sr: int = 16000) -> Dict:
        """
        Analyze a single audio chunk in real-time.
        
        Args:
            audio_data: Audio samples (numpy array)
            sr: Sample rate
        
        Returns:
            Dictionary with detection results
        """
        start_time = time.time()
        
        try:
            # Normalize audio length to 3.5 seconds for consistent analysis
            audio_normalized = prepare_audio_for_analysis(audio_data, sr, method='best')
            
            logger.info(f"Audio normalized: {len(audio_data)/sr:.2f}s -> {len(audio_normalized)/sr:.2f}s")
            
            # Save temporary audio for processing
            import tempfile
            import soundfile as sf
            import time as time_module
            
            # Create temp file with explicit delete=False
            tmp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            tmp_path = tmp_file.name
            tmp_file.close()  # Close file handle immediately
            
            # Write audio
            sf.write(tmp_path, audio_normalized, sr)
            
            # Small delay to ensure file is written
            time_module.sleep(0.05)
            
            # Extract features from normalized audio
            mfcc = extract_mfcc_features_fast(audio_normalized, sr)
            stft = extract_stft_features_fast(audio_normalized, sr)
            phase = extract_phase_continuity_features_fast(audio_normalized, sr)
            jitter = calculate_jitter(tmp_path)
            
            # Clean up temp file - try multiple times if locked
            for attempt in range(3):
                try:
                    Path(tmp_path).unlink()
                    break
                except Exception as e:
                    if attempt < 2:
                        time_module.sleep(0.1)
                    else:
                        logger.warning(f"Could not delete temp file: {e}")
            
            # Combine features
            features = {
                **mfcc,
                **stft,
                **phase,
                'jitter': jitter
            }
            
            # Make prediction
            is_fake, confidence, risk_level = self._predict(features)
            
            # Calculate deviation from baseline
            baseline_deviation = self._calculate_baseline_deviation(features)
            
            # Store in history
            self.feature_history.append(features)
            self.prediction_buffer.append(is_fake)
            
            # Smooth predictions
            smoothed_prediction = sum(self.prediction_buffer) / len(self.prediction_buffer)
            
            processing_time = time.time() - start_time
            
            result = {
                'timestamp': time.time(),
                'is_fake': bool(is_fake),
                'confidence': float(confidence),
                'risk_level': risk_level,
                'smoothed_fake_probability': float(smoothed_prediction),
                'features': features,  # Include ALL features, not just a subset
                'baseline_deviation': baseline_deviation,
                'processing_time_ms': processing_time * 1000,
                'verdict': self._get_verdict(is_fake, confidence, risk_level),
                'audio_duration': len(audio_normalized) / sr
            }
            
            logger.info(f"Chunk analyzed: {result['verdict']} (confidence: {confidence:.2%})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing chunk: {e}")
            return {
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _predict(self, features: Dict) -> Tuple[bool, float, str]:
        """
        Make prediction based on features.
        
        Returns:
            Tuple of (is_fake, confidence, risk_level)
        """
        if self.classifier['type'] == 'threshold':
            feature_name = self.classifier['feature']
            threshold = self.classifier['threshold']
            
            feature_value = features.get(feature_name, 0)
            
            # Determine if fake
            is_fake = feature_value > threshold
            
            # Calculate confidence
            distance = abs(feature_value - threshold)
            confidence = min(distance / threshold, 1.0)
            
            # Determine risk level
            if feature_value > threshold * 1.5:
                risk_level = 'HIGH'
            elif feature_value > threshold * 1.2:
                risk_level = 'MEDIUM'
            elif feature_value > threshold * 0.8:
                risk_level = 'LOW'
            else:
                risk_level = 'MINIMAL'
            
            return is_fake, confidence, risk_level
        
        return False, 0.5, 'UNKNOWN'
    
    def _calculate_baseline_deviation(self, features: Dict) -> Optional[float]:
        """Calculate deviation from baseline features."""
        if not self.baseline_features:
            return None
        
        # Compare key features
        key_features = [
            'phase_discontinuity_mean',
            'spectral_centroid_mean',
            'jitter'
        ]
        
        deviations = []
        for feature in key_features:
            baseline_val = self.baseline_features.get(feature, 0)
            current_val = features.get(feature, 0)
            
            if baseline_val != 0:
                deviation = abs(current_val - baseline_val) / baseline_val
                deviations.append(deviation)
        
        return float(np.mean(deviations)) if deviations else None
    
    def _get_verdict(self, is_fake: bool, confidence: float, risk_level: str) -> str:
        """Generate human-readable verdict."""
        if is_fake:
            if risk_level == 'HIGH':
                return " SYNTHETIC VOICE DETECTED - HIGH CONFIDENCE"
            elif risk_level == 'MEDIUM':
                return " LIKELY SYNTHETIC - MEDIUM CONFIDENCE"
            else:
                return " POSSIBLY SYNTHETIC - LOW CONFIDENCE"
        else:
            if confidence > 0.8:
                return " AUTHENTIC VOICE - HIGH CONFIDENCE"
            elif confidence > 0.5:
                return " LIKELY AUTHENTIC - MEDIUM CONFIDENCE"
            else:
                return " UNCERTAIN - REQUIRES MANUAL REVIEW"
    
    def get_statistics(self) -> Dict:
        """Get statistics from recent predictions."""
        if not self.prediction_buffer:
            return {}
        
        fake_count = sum(self.prediction_buffer)
        total_count = len(self.prediction_buffer)
        
        return {
            'total_chunks_analyzed': total_count,
            'fake_chunks': fake_count,
            'authentic_chunks': total_count - fake_count,
            'fake_percentage': (fake_count / total_count) * 100,
            'buffer_size': self.buffer_size
        }
    
    def reset(self):
        """Reset detector state."""
        self.prediction_buffer.clear()
        self.feature_history.clear()
        logger.info("Detector state reset")


class StreamProcessor:
    """
    Process continuous audio streams for real-time detection.
    """
    
    def __init__(self, detector: RealtimeVoiceDetector, chunk_duration: float = 2.0):
        """
        Initialize stream processor.
        
        Args:
            detector: RealtimeVoiceDetector instance
            chunk_duration: Duration of each audio chunk in seconds
        """
        self.detector = detector
        self.chunk_duration = chunk_duration
        self.sample_rate = 16000
        self.chunk_size = int(chunk_duration * self.sample_rate)
        self.buffer = np.array([])
        
        logger.info(f"StreamProcessor initialized (chunk_duration={chunk_duration}s)")
    
    def process_stream(self, audio_data: np.ndarray, sr: int = 16000):
        """
        Process incoming audio stream data.
        
        Args:
            audio_data: New audio samples
            sr: Sample rate
        
        Yields:
            Detection results for each complete chunk
        """
        # Resample if needed
        if sr != self.sample_rate:
            audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.sample_rate)
        
        # Add to buffer
        self.buffer = np.concatenate([self.buffer, audio_data])
        
        # Process complete chunks
        while len(self.buffer) >= self.chunk_size:
            chunk = self.buffer[:self.chunk_size]
            self.buffer = self.buffer[self.chunk_size:]
            
            result = self.detector.analyze_chunk(chunk, self.sample_rate)
            yield result
    
    def flush(self):
        """Process remaining buffer data."""
        if len(self.buffer) > 0:
            result = self.detector.analyze_chunk(self.buffer, self.sample_rate)
            self.buffer = np.array([])
            return result
        return None


if __name__ == "__main__":
    # Example usage
    detector = RealtimeVoiceDetector()
    
    # Set baseline (optional)
    # detector.set_baseline("path/to/authentic_voice.wav")
    
    # Test with a sample file
    test_file = "small_data/sample_0_labelunknown.wav"
    if Path(test_file).exists():
        y, sr = librosa.load(test_file, sr=16000)
        result = detector.analyze_chunk(y, sr)
        
        print("\n" + "=" * 80)
        print("REAL-TIME DETECTION TEST")
        print("=" * 80)
        print(f"Verdict: {result['verdict']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Risk Level: {result['risk_level']}")
        print(f"Processing Time: {result['processing_time_ms']:.2f}ms")
        print("=" * 80)
