import os
from typing import Dict, Any
import json
import numpy as np
import librosa
from pathlib import Path
from joblib import Parallel, delayed
from tqdm import tqdm

from backend.audio_normalizer import normalize_audio
from backend.utils import calculate_jitter, calculate_phase_discontinuity

def extract_features(audio_path, sr=16000, n_mfcc=40):
    """
    Extract MFCC, Spectral, and Phase continuity features for a single file.
    Returns a dictionary of features.
    """
    try:
        if not os.path.exists(audio_path):
            print(f"File not found: {audio_path}")
            return None
            
        import soundfile as sf
        y, orig_sr = sf.read(audio_path)
        
        # If stereo, librosa to_mono expects shape (2, n), soundfile gives (n, 2)
        if len(y.shape) > 1:
            y = y.mean(axis=1)
            
        # Normalize to exactly 3.5 seconds
        y, _ = normalize_audio(y, orig_sr, target_duration=3.5)
        
        features: Dict[str, Any] = {}
        
        # 1. Extract MFCCs
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
        mfccs_delta = librosa.feature.delta(mfccs)
        
        features["mfcc_mean"] = mfccs.mean(axis=1).tolist()
        features["mfcc_std"] = mfccs.std(axis=1).tolist()
        features["mfcc_delta_mean"] = mfccs_delta.mean(axis=1).tolist()
        
        # 2. Extract Spectral Features
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        
        features["spectral_centroid_mean"] = float(spectral_centroid.mean())
        features["spectral_centroid_std"] = float(spectral_centroid.std())
        features["spectral_bandwidth_mean"] = float(spectral_bandwidth.mean())
        features["spectral_bandwidth_std"] = float(spectral_bandwidth.std())
        features["spectral_contrast_mean"] = spectral_contrast.mean(axis=1).tolist()
        features["spectral_contrast_std"] = spectral_contrast.std(axis=1).tolist()
        
        # 3. Phase Analysis (CRUCIAL for AI Detection)
        phase_metrics = calculate_phase_discontinuity(y)
        for k, v in phase_metrics.items():
            features[f"phase_{k}"] = v
            
        # 4. Jitter
        features["jitter"] = calculate_jitter(y, sr)
        
        # File info
        features["filename"] = Path(audio_path).name
        
        # Add labels if available (e.g. dataset directory names)
        path_str = str(audio_path).lower()
        if 'real' in path_str:
            features['label'] = 'real'
        elif 'fake' in path_str or 'ai' in path_str:
            features['label'] = 'fake'
        else:
            features['label'] = None
            
        return features
        
    except Exception as e:
        import traceback
        print(f"Error processing {audio_path}: {e}")
        print(traceback.format_exc())
        return None

def process_dataset_parallel(data_dir, output_file='features.json', n_jobs=-1):
    """
    Process all .wav files in a directory in parallel using joblib.
    """
    if not os.path.exists(data_dir):
        print(f"Directory {data_dir} does not exist.")
        return None
        
    # Get all wav files
    wav_files = []
    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.wav'):
                wav_files.append(os.path.join(root, file))
                
    if not wav_files:
        print(f"No .wav files found in {data_dir}")
        return None
        
    print(f"Found {len(wav_files)} files. Extracting features...")
    
    # Process files in parallel
    results = Parallel(n_jobs=n_jobs)(
        delayed(extract_features)(f) for f in tqdm(wav_files, desc="Extracting")
    )
    
    # Filter out failed extractions
    valid_results = [r for r in results if r is not None]
    
    if valid_results:
        # Avoid creating massive lists if we just need a dict mapping
        feature_dict = {r["filename"]: r for r in valid_results}
        
        with open(output_file, 'w') as f:
            json.dump(feature_dict, f, indent=4)
            
        print(f"Successfully extracted features for {len(valid_results)} files. Saved to {output_file}")
        return feature_dict
    else:
        print("Feature extraction failed for all files.")
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
        out_file = "features.json" if len(sys.argv) == 2 else sys.argv[2]
        process_dataset_parallel(data_dir, out_file)
    else:
        print("Usage: python feature_extraction_fast.py <data_dir> [output_file.json]")
