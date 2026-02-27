from huggingface_hub import snapshot_download
from transformers import Wav2Vec2Model, Wav2Vec2Processor
import warnings
warnings.filterwarnings("ignore")

print("Downloading SpeechBrain locally (no symlinks)...")
snapshot_download(repo_id="speechbrain/spkrec-ecapa-voxceleb", local_dir="pretrained_models/spkrec-ecapa-voxceleb", max_workers=1)
print("SpeechBrain Download complete!")

print("Downloading Wav2Vec2 model...")
Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base")
Wav2Vec2Model.from_pretrained("facebook/wav2vec2-base")
print("All model weights successfully cached for Kural-Pulse.")
