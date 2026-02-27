import traceback
import sys
import torchaudio

if not hasattr(torchaudio, 'list_audio_backends'):
    torchaudio.list_audio_backends = lambda: ['soundfile']

import os
import shutil
if os.name == 'nt':
    def _safe_symlink(src, dst, target_is_directory=False, **kwargs):
        try:
            if target_is_directory:
                shutil.copytree(str(src), str(dst), dirs_exist_ok=True)
            else:
                shutil.copy(str(src), str(dst))
        except Exception as e:
            print(f"Safe symlink failed: {e}")
    os.symlink = _safe_symlink

import huggingface_hub
_orig_hf = huggingface_hub.hf_hub_download
def _patched_hf(*args, **kwargs):
    kwargs.pop("use_auth_token", None)
    return _orig_hf(*args, **kwargs)
huggingface_hub.hf_hub_download = _patched_hf

import speechbrain.utils.fetching
speechbrain.utils.fetching.huggingface_hub.hf_hub_download = _patched_hf

from speechbrain.inference.speaker import EncoderClassifier

try:
    m = EncoderClassifier.from_hparams(source='pretrained_models/spkrec-ecapa-voxceleb', savedir='pretrained_models/spkrec-ecapa-voxceleb')
    print('SUCCESS')
except Exception as e:
    with open('trace.txt', 'w') as f:
        traceback.print_exc(file=f)

