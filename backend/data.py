from datasets import load_dataset
import os
import scipy.io.wavfile as wavfile
import numpy as np
import re


class DataPreparationError(Exception):
    pass


def safe_filename(name):
    """Sanitize filename by replacing invalid characters."""
    return re.sub(r"[\\/*?:\"<>|]", "_", name)


# Create directory for data
os.makedirs("data", exist_ok=True)

print("📡 Downloading dataset metadata...")
# Load the ASVspoof5 dataset from Hugging Face
dataset = load_dataset("jungjee/asvspoof5", split="train", streaming=True)

# Pull only 500 samples
subset_size = 500
subset = dataset.take(subset_size)

print(f"💾 Saving {subset_size} samples locally...")
processed_labels = set()
for i, sample in enumerate(subset):
    try:
        # Extract audio data and sampling rate (handle missing keys gracefully)
        if "audio" not in sample or "array" not in sample["audio"]:
            raise KeyError("Missing 'audio' key")

        audio_data = sample["audio"]["array"]
        sampling_rate = sample["audio"]["sampling_rate"]

        # Handle label retrieval with multiple fallbacks
        label = sample.get("label", "unknown")
        if label == "unknown":
            label = sample.get("attack_type", "unknown")

        # Sanitize filename to prevent invalid characters
        safe_label = safe_filename(label)
        filename = f"data/sample_{i}_{safe_label}.wav"

        # Save as WAV file
        wavfile.write(filename, sampling_rate, audio_data)

        processed_labels.add(safe_label)
    except Exception as e:
        print(f"⚠️ Error processing sample {i}: {str(e)}")
        continue

print("✅ Data preparation complete.")
print(f"Processed labels: {', '.join(processed_labels)}")