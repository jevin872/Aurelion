"""
Audio normalization and segmentation for consistent analysis.
Handles audio of different lengths by extracting and analyzing fixed-duration segments.
"""

import numpy as np
import librosa


def normalize_audio_length(audio_data, sr=16000, target_duration=3.5):
    """
    Normalize audio to target duration (default 3.5 seconds).
    
    Args:
        audio_data: Audio samples
        sr: Sample rate
        target_duration: Target duration in seconds
    
    Returns:
        Normalized audio of target duration
    """
    target_samples = int(target_duration * sr)
    current_samples = len(audio_data)
    
    if current_samples >= target_samples:
        # Take middle section if longer
        start = (current_samples - target_samples) // 2
        return audio_data[start:start + target_samples]
    else:
        # Pad with silence if shorter
        padding = target_samples - current_samples
        pad_left = padding // 2
        pad_right = padding - pad_left
        return np.pad(audio_data, (pad_left, pad_right), mode='constant')


def extract_segments(audio_data, sr=16000, segment_duration=3.5, overlap=0.5):
    """
    Extract overlapping segments from audio for multi-segment analysis.
    
    Args:
        audio_data: Audio samples
        sr: Sample rate
        segment_duration: Duration of each segment in seconds
        overlap: Overlap between segments (0-1)
    
    Returns:
        List of audio segments
    """
    segment_samples = int(segment_duration * sr)
    hop_samples = int(segment_samples * (1 - overlap))
    
    segments = []
    
    # If audio is shorter than segment duration, just return normalized version
    if len(audio_data) < segment_samples:
        return [normalize_audio_length(audio_data, sr, segment_duration)]
    
    # Extract overlapping segments
    for start in range(0, len(audio_data) - segment_samples + 1, hop_samples):
        segment = audio_data[start:start + segment_samples]
        segments.append(segment)
    
    # Ensure we have at least 2 segments for comparison
    if len(segments) < 2:
        # Take beginning and end
        segments = [
            audio_data[:segment_samples],
            audio_data[-segment_samples:]
        ]
    
    return segments


def get_best_segment(audio_data, sr=16000, target_duration=3.5):
    """
    Get the best quality segment from audio (highest energy).
    
    Args:
        audio_data: Audio samples
        sr: Sample rate
        target_duration: Target duration in seconds
    
    Returns:
        Best quality segment
    """
    segments = extract_segments(audio_data, sr, target_duration, overlap=0.3)
    
    if len(segments) == 1:
        return segments[0]
    
    # Calculate energy for each segment
    energies = [np.sum(segment ** 2) for segment in segments]
    
    # Return segment with highest energy (most speech content)
    best_idx = np.argmax(energies)
    return segments[best_idx]


def analyze_multiple_segments(audio_data, sr, feature_extractor, num_segments=3):
    """
    Analyze multiple segments and aggregate results.
    
    Args:
        audio_data: Audio samples
        sr: Sample rate
        feature_extractor: Function to extract features from audio
        num_segments: Number of segments to analyze
    
    Returns:
        Aggregated features from multiple segments
    """
    # Extract segments
    segments = extract_segments(audio_data, sr, segment_duration=3.5, overlap=0.3)
    
    # Limit to num_segments
    if len(segments) > num_segments:
        # Select segments with highest energy
        energies = [np.sum(seg ** 2) for seg in segments]
        top_indices = np.argsort(energies)[-num_segments:]
        segments = [segments[i] for i in top_indices]
    
    # Extract features from each segment
    all_features = []
    for segment in segments:
        features = feature_extractor(segment, sr)
        all_features.append(features)
    
    # Aggregate features (median for robustness)
    aggregated = {}
    
    for key in all_features[0].keys():
        if key in ['filename', 'label']:
            aggregated[key] = all_features[0][key]
            continue
        
        values = []
        for features in all_features:
            val = features.get(key)
            if isinstance(val, list):
                values.append(np.array(val))
            else:
                values.append(val)
        
        if isinstance(values[0], np.ndarray):
            # For arrays (like MFCC), take median across segments
            aggregated[key] = np.median(values, axis=0).tolist()
        else:
            # For scalars, take median
            aggregated[key] = float(np.median(values))
    
    return aggregated


def prepare_audio_for_analysis(audio_data, sr=16000, method='best'):
    """
    Prepare audio for analysis by normalizing length.
    
    Args:
        audio_data: Audio samples
        sr: Sample rate
        method: 'best' (highest energy), 'middle' (center), or 'normalize' (pad/trim)
    
    Returns:
        Prepared audio segment
    """
    if method == 'best':
        return get_best_segment(audio_data, sr)
    elif method == 'middle':
        return normalize_audio_length(audio_data, sr)
    elif method == 'normalize':
        return normalize_audio_length(audio_data, sr)
    else:
        return get_best_segment(audio_data, sr)


if __name__ == "__main__":
    # Test the normalizer
    print("=" * 80)
    print("AUDIO NORMALIZER - TEST")
    print("=" * 80)
    
    # Simulate different length audios
    sr = 16000
    
    test_cases = [
        ("Short (2s)", np.random.randn(2 * sr)),
        ("Target (3.5s)", np.random.randn(int(3.5 * sr))),
        ("Long (10s)", np.random.randn(10 * sr)),
    ]
    
    for name, audio in test_cases:
        print(f"\n{name}:")
        print(f"  Original: {len(audio)/sr:.2f}s ({len(audio)} samples)")
        
        normalized = normalize_audio_length(audio, sr)
        print(f"  Normalized: {len(normalized)/sr:.2f}s ({len(normalized)} samples)")
        
        segments = extract_segments(audio, sr)
        print(f"  Segments: {len(segments)} x {len(segments[0])/sr:.2f}s")
        
        best = get_best_segment(audio, sr)
        print(f"  Best segment: {len(best)/sr:.2f}s")
    
    print("\n" + "=" * 80)
    print("All audio normalized to 3.5 seconds for consistent analysis!")
    print("=" * 80)
