import os
import numpy as np
import soundfile as sf
import librosa

def generate_mock_audio(filename, duration=4.0, sr=16000, is_ai=False):
    """
    Generates realistic looking synthetic audio features based on whether it is AI or Human.
    """
    t = np.linspace(0, duration, int(sr * duration))
    
    if not is_ai:
        # HUMAN VOICE: Harmonic complex tone (vowel-like) + noise (fricative-like)
        # Base fundamental frequency
        f0 = 150.0 + np.random.randn() * 20.0 
        
        # Add harmonics
        y = np.sin(2 * np.pi * f0 * t) 
        y += 0.5 * np.sin(2 * np.pi * f0 * 2 * t)
        y += 0.25 * np.sin(2 * np.pi * f0 * 3 * t)
        
        # Add slight natural jitter (frequency modulation)
        mod = 0.01 * np.sin(2 * np.pi * 5 * t)
        y += np.sin(2 * np.pi * f0 * (t + mod))
        
        # Add breath noise
        y += np.random.randn(len(t)) * 0.05
    else:
        # AI VOICE: More rigid, contains very distinct phase artifacts.
        f0 = 150.0
        # Rigid harmonics
        y = np.sin(2 * np.pi * f0 * t) 
        y += 0.5 * np.sin(2 * np.pi * f0 * 2.05 * t) # Slightly off-harmonic (common AI artifact)
        
        # Add phase jump (simulating vocoder artifacts)
        jump_idx = len(t) // 2
        y[jump_idx:] = y[jump_idx:] * -1
        
        # Mechanical rigidity / Lack of natural noise
        y += np.random.randn(len(t)) * 0.001

    # Apply envelope
    envelope = np.ones_like(y)
    fade_len = int(sr * 0.1)
    envelope[:fade_len] = np.linspace(0, 1, fade_len)
    envelope[-fade_len:] = np.linspace(1, 0, fade_len)
    y = y * envelope
    
    # Normalize
    y = y / np.max(np.abs(y))
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    sf.write(filename, y, sr)
    return filename

print("Regenerating Small Data...")
for i in range(250):
    is_ai = (i % 5 == 0) # 20% AI
    generate_mock_audio(f"small_data/sample_{i}_labelunknown.wav", is_ai=is_ai)

print("Regenerating Datasets...")
os.makedirs("dataset/real", exist_ok=True)
os.makedirs("dataset/fake", exist_ok=True)

# Generate baseline realistic sample
generate_mock_audio("dataset/real/clip_0.wav", is_ai=False)
# Generate a slightly different human sample (different speaker)
generate_mock_audio("dataset/real/clip_1.wav", is_ai=False)
generate_mock_audio("dataset/real/clip_2.wav", is_ai=False)

# Generate AI sample
generate_mock_audio("dataset/fake/Ali.wav", is_ai=True)
generate_mock_audio("dataset/fake/Sarah.wav", is_ai=True)

print("Finished regenerating test audio datasets!")
