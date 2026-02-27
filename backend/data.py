from datasets import load_dataset, Audio
import os
import scipy.io.wavfile as wavfile
import numpy as np

# Create directory for data
os.makedirs("data", exist_ok=True)

print("📡 Downloading dataset metadata...")
# Load the ASVspoof5 dataset from Hugging Face
dataset = load_dataset("jungjee/asvspoof5", split="train", streaming=True)

# --- FIX CASTERROR ---
# Explicitly cast the column containing the audio files to Audio()
# Based on the error, the raw FLAC content is in the 'flac' column
dataset = dataset.cast_column("flac", Audio(sampling_rate=16000))

# Pull only 500 samples
subset_size = 500
subset = dataset.take(subset_size)

print(f"💾 Saving {subset_size} samples locally...")
for i, sample in enumerate(subset):
    try:
        # Now 'flac' contains the decoded audio data after casting
        audio_data = sample["flac"]["array"]
        sampling_rate = sample["flac"]["sampling_rate"]

        # Handle label retrieval
        label = sample.get("label", "unknown")
        if label == "unknown":
            label = sample.get("attack_type", "unknown")

        # Filename safe label
        safe_label = "".join(c for c in str(label) if c.isalnum() or c in ("-", "_"))
        filename = f"data/sample_{i}_{safe_label}.wav"

        # Save as WAV file
        wavfile.write(filename, sampling_rate, audio_data)

    except Exception as e:
        print(f"❌ Error processing sample {i}: {str(e)}")
        continue

print("✅ Data preparation complete.")
