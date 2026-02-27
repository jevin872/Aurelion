import librosa
import numpy as np

def normalize_audio(audio_data, sr=16000, target_duration=3.5):
    """
    Normalizes audio by strictly keeping it mono, resampling to the standard 
    sample rate (16000), and forcing the duration exactly to target_duration.
    
    Args:
        audio_data: Input audio waveform (numpy array)
        sr: Sample rate of the input audio
        target_duration: The target duration in seconds (Default 3.5s)
        
    Returns:
        tuple: (normalized_audio_array, target_sample_rate)
    """
    target_sr = 16000
    
    # 1. Ensure audio is Mono
    if len(audio_data.shape) > 1:
        audio_data = librosa.to_mono(audio_data)
        
    # 2. Resample if necessary
    if sr != target_sr:
        audio_data = librosa.resample(y=audio_data, orig_sr=sr, target_sr=target_sr)
        
    # 3. Force exact length
    target_length = int(target_sr * target_duration)
    
    if len(audio_data) > target_length:
        # Truncate
        audio_data = audio_data[:target_length]
    elif len(audio_data) < target_length:
        # Pad with zeros
        audio_data = np.pad(audio_data, (0, target_length - len(audio_data)), 'constant')
        
    return audio_data, target_sr
