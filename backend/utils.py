import librosa
import numpy as np
import os

# Try to import parselmouth, but make it optional
try:
    from parselmouth.praat import call
    import parselmouth
    PARSELMOUTH_AVAILABLE = True
except ImportError:
    PARSELMOUTH_AVAILABLE = False
    print("Warning: parselmouth not available. Jitter calculation will be simplified.")


def calculate_jitter(audio_path):
    """Calculates local jitter using Praat (if available) or simplified method."""
    if not os.path.exists(audio_path):
        return 0.0
    
    if PARSELMOUTH_AVAILABLE:
        try:
            sound = parselmouth.Sound(audio_path)
            point_process = call(sound, "To PointProcess (periodic, cc)", 75, 500)
            jitter = call(point_process, "Get jitter (local)", 0.0, 0.0, 0.0001, 0.02, 1.3)
            return jitter
        except Exception:
            pass
    
    # Fallback: simplified jitter calculation
    try:
        y, sr = librosa.load(audio_path, sr=None)
        # Estimate pitch periods
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        # Calculate variation in pitch periods as a proxy for jitter
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        if len(pitch_values) > 1:
            pitch_array = np.array(pitch_values)
            jitter = np.std(np.diff(pitch_array)) / np.mean(pitch_array) if np.mean(pitch_array) > 0 else 0.0
            return float(jitter)
    except Exception:
        pass
    
    return 0.0


def extract_mfcc(audio_path):
    """Extracts MFCCs for speaker identification (counterpart check)."""
    y, sr = librosa.load(audio_path, sr=None)
    # Extract 13 MFCC coefficients and take the mean across time
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    return np.mean(mfcc, axis=1)


def analyze_phase_discontinuity(audio_path):
    """Computes STFT and measures phase inconsistencies."""
    y, sr = librosa.load(audio_path, sr=None)

    # 1. Short-Time Fourier Transform (STFT)
    stft = librosa.stft(y)

    # 2. Extract Phase Information
    phase = np.angle(stft)

    # 3. Compute Phase Derivative (detects sudden jumps/inconsistencies)
    phase_derivative = np.diff(phase, axis=1)

    # 4. Return mean inconsistency score
    return np.mean(np.abs(phase_derivative))


def analyze_voice_liveness(file_path):
    """Combines all feature extraction for classification."""

    #

    jitter_score = calculate_jitter(file_path)
    phase_score = analyze_phase_discontinuity(file_path)
    mfcc_features = extract_mfcc(file_path)

    return {
        "jitter": jitter_score,
        "phase_inconsistency": phase_score,
        "mfcc_mean": mfcc_features.tolist(),  # Convert numpy array to list for JSON
    }
