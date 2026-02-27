import numpy as np
import librosa

def calculate_jitter(y, sr):
    """
    Calculate voice jitter (cycle-to-cycle variation in pitch).
    Returns a small float or 0 if extraction fails.
    """
    try:
        f0, voiced_flag, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr)
        
        # Get only the voiced frames
        f0_voiced = f0[voiced_flag]
        
        if len(f0_voiced) < 2:
            return 0.0
            
        periods = 1.0 / f0_voiced
        
        # Absolute differences between consecutive periods
        period_diffs = np.abs(np.diff(periods))
        
        mean_period = np.mean(periods)
        mean_diff = np.mean(period_diffs)
        
        if mean_period == 0:
            return 0.0
            
        # Jitter is mean_diff / mean_period
        jitter = mean_diff / mean_period
        return float(jitter)
        
    except Exception:
        return 0.0

def calculate_phase_discontinuity(y, n_fft=2048, hop_length=512):
    """
    Calculates the phase discontinuity of the audio signal.
    This is extremely important for detecting AI generated voices.
    """
    try:
        # Compute STFT
        D = librosa.stft(y, n_fft=n_fft, hop_length=hop_length)
        
        # Get phase
        phase = np.angle(D)
        
        # Unwrap phase along time axis (axis=1)
        unwrapped_phase = np.unwrap(phase, axis=1)
        
        # Compute second derivative of phase (phase acceleration)
        # Phase jumps often occur when vocoders synthetically generate audio
        phase_diff = np.diff(unwrapped_phase, axis=1)
        phase_diff2 = np.diff(phase_diff, axis=1)
        
        # Calculate mean absolute discontinuity across frequency bins and time
        discontinuity = np.mean(np.abs(phase_diff2))
        
        # Other useful metrics
        unwrapped_mean = np.mean(np.abs(unwrapped_phase))
        consistency = np.std(phase_diff, axis=1).mean()
        max_disc = np.max(np.abs(phase_diff2))
        
        return {
            'discontinuity_mean': float(discontinuity),
            'discontinuity_std': float(np.std(np.abs(phase_diff2))),
            'discontinuity_max': float(max_disc),
            'unwrapped_mean': float(unwrapped_mean),
            'unwrapped_std': float(np.std(unwrapped_phase)),
            'consistency_mean': float(consistency),
            'consistency_std': float(np.std(np.std(phase_diff, axis=1)))
        }
    except Exception:
        return {
            'discontinuity_mean': 0.0,
            'discontinuity_std': 0.0,
            'discontinuity_max': 0.0,
            'unwrapped_mean': 0.0,
            'unwrapped_std': 0.0,
            'consistency_mean': 0.0,
            'consistency_std': 0.0
        }
