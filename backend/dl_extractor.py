import os
from typing import Dict, Any
import torch
import torchaudio

# Monkeypatch torchaudio for SpeechBrain backwards compatibility BEFORE importing it
if not hasattr(torchaudio, 'list_audio_backends'):
    torchaudio.list_audio_backends = lambda: ['soundfile']

import shutil
if os.name == 'nt':
    def _safe_symlink(src, dst, target_is_directory=False, **kwargs):
        try:
            if target_is_directory:
                shutil.copytree(str(src), str(dst), dirs_exist_ok=True)
            else:
                shutil.copy(str(src), str(dst))
        except Exception as e:
            print(f"Safe symlink copy failed: {e}")
    os.symlink = _safe_symlink

import huggingface_hub

_orig_snapshot_download = huggingface_hub.snapshot_download
def _patched_snapshot_download(*args, **kwargs):
    kwargs.pop("use_auth_token", None)
    return _orig_snapshot_download(*args, **kwargs)
huggingface_hub.snapshot_download = _patched_snapshot_download

_orig_hf_hub_download = huggingface_hub.hf_hub_download
def _patched_hf_hub_download(*args, **kwargs):
    kwargs.pop("use_auth_token", None)
    return _orig_hf_hub_download(*args, **kwargs)
huggingface_hub.hf_hub_download = _patched_hf_hub_download

import speechbrain.utils.fetching
speechbrain.utils.fetching.huggingface_hub.hf_hub_download = _patched_hf_hub_download

import librosa
import numpy as np
from pathlib import Path
from transformers import Wav2Vec2Processor, Wav2Vec2Model
from speechbrain.inference.speaker import EncoderClassifier

# We will use dotenv to occasionally check env overrides or HF tokens if needed
from dotenv import load_dotenv
load_dotenv()

class KuralPulseExtractor:
    def __init__(self, device=None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        print(f"Initializing Kural-Pulse Extractor on {self.device}...")
        
        # Monkeypatch torchaudio for SpeechBrain backwards compatibility
        if not hasattr(torchaudio, 'list_audio_backends'):
            torchaudio.list_audio_backends = lambda: ['soundfile']
            
        # 1. SpeechBrain Speaker Embedding Model (Identity Check)
        # Using ECAPA-TDNN trained on VoxCeleb loaded LOCALLY
        try:
            self.speaker_model = EncoderClassifier.from_hparams(
                source="pretrained_models/spkrec-ecapa-voxceleb",
                savedir="pretrained_models/spkrec-ecapa-voxceleb",
                run_opts={"device": self.device}
            )
        except Exception as e:
            print(f"Failed to load SpeechBrain model: {e}")
            self.speaker_model = None

        # 2. Wav2Vec 2.0 (Deepfake & AI Synthetic Detection)
        # Using base model to analyze latent acoustic states and find artifacts
        try:
            self.w2v_processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base")
            self.w2v_model = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-base").to(self.device)
            self.w2v_model.eval()
        except Exception as e:
            print(f"Failed to load Wav2Vec2 model: {e}")
            self.w2v_model = None

    def preprocess_audio(self, audio_path, target_sr=16000, target_duration=None):
        """Load and normalize audio uniformly for DL models."""
        try:
            y, sr = librosa.load(audio_path, sr=target_sr)
            
            # Simple VAD (Voice Activity Detection): Trim leading/trailing silence
            y, _ = librosa.effects.trim(y, top_db=30)
            
            if target_duration:
                target_length = int(target_duration * target_sr)
                if len(y) > target_length:
                    y = y[:target_length]
                else:
                    y = np.pad(y, (0, max(0, target_length - len(y))))
            
            return y, target_sr
        except Exception as e:
            print(f"Preprocess error for {audio_path}: {e}")
            return None, None

    def extract_identity_embedding(self, audio_path):
        """Extracts X-Vector biological identity using SpeechBrain."""
        if not self.speaker_model:
            return None
        
        try:
            # Avoid torchaudio backend issues, load with librosa/soundfile and convert to tensor
            y, sr = librosa.load(audio_path, sr=16000)
            
            # Convert to torch tensor
            signal = torch.tensor(y, dtype=torch.float32).unsqueeze(0).to(self.device)
            # signal shape: [batch, samples]
                
            embeddings = self.speaker_model.encode_batch(signal)
            # Embedding shape: [bat, 1, channels]
            return embeddings.squeeze().cpu().numpy()
        except Exception as e:
            import traceback
            print(f"SpeechBrain extraction error: {e}")
            print(traceback.format_exc())
            return None

    def extract_synthetic_artifacts(self, y, sr):
        """
        Calculates Phase Discontinuity & Wav2Vec2 latent variance to detect 
        synthetic generation artifacts.
        """
        features: Dict[str, Any] = {}
        
        # 1. Wav2Vec 2.0 Latent Variance Analysis
        if self.w2v_model and self.w2v_processor:
            try:
                # Processor expects 1D array of 16kHz audio
                inputs = self.w2v_processor(y, sampling_rate=sr, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = self.w2v_model(**inputs)
                    last_hidden_states = outputs.last_hidden_state
                    
                # AI voices often have lower variance in deep acoustic hidden states
                # due to rigid generation parameters compared to natural biological drift.
                variance = torch.var(last_hidden_states, dim=1).mean().item()
                features["w2v_latent_variance"] = variance
            except Exception as e:
                print(f"Wav2Vec2 extraction error: {e}")
                features["w2v_latent_variance"] = 0.0

        # 2. Phase Discontinuity Analysis (Digital STFT Stitches)
        # Deepfakes & Vocoders often struggle with phase alignment across frames.
        try:
            stft = librosa.stft(y, n_fft=2048, hop_length=512)
            phase = np.angle(stft)
            # Calculate absolute phase difference between consecutive frames
            phase_diff = np.abs(np.diff(phase, axis=1))
            # Normalize phase diff to wrap around Pi
            phase_diff = np.mod(phase_diff + np.pi, 2 * np.pi) - np.pi
            # Vocoders produce localized sharp discontinuities, increasing variance of the differences
            features["phase_discontinuity_var"] = float(np.var(phase_diff))
            features["phase_discontinuity_mean"] = float(np.mean(np.abs(phase_diff)))
        except Exception as e:
            features["phase_discontinuity_var"] = 0.0
            features["phase_discontinuity_mean"] = 0.0

        # 3. Traditional Acoustic MFCC (Baseline Resonance)
        try:
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
            features["mfcc_mean"] = mfccs.mean(axis=1).tolist()
        except Exception:
            features["mfcc_mean"] = []

        return features

    def get_full_profile(self, audio_path):
        """Runs the entire biological + anti-spoof extraction pipeline."""
        y, sr = self.preprocess_audio(audio_path, target_sr=16000)
        if y is None:
            return None

        # Deep Identity Embedding
        identity = self.extract_identity_embedding(audio_path)
        
        # Biological Acoustic & Synthetic Ghost Analysis
        artifact_metrics = self.extract_synthetic_artifacts(y, sr)
        
        return {
            "identity_embedding": identity.tolist() if identity is not None else [],
            "artifacts": artifact_metrics
        }

if __name__ == "__main__":
    print("Testing Extractor Initialization...")
    extractor = KuralPulseExtractor()
    print("Pre-loading complete.")
