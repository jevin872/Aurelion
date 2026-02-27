import time
from backend.dl_extractor import KuralPulseExtractor

extractor = KuralPulseExtractor()

# Generate a quick dummy wav file to test
import numpy as np
import soundfile as sf
y = np.random.randn(16000 * 3) # 3 seconds noise
sf.write("dummy_test.wav", y, 16000)

print("Running baseline extraction...")
start = time.time()
profile = extractor.get_full_profile("dummy_test.wav")
end = time.time()

print(f"Extraction completed in: {(end - start) * 1000:.2f} ms")
if profile:
    print(f"Identity Vector Size: {len(profile.get('identity_embedding', []))}")
    print(f"Artifacts computed: {list(profile.get('artifacts', {}).keys())}")
else:
    print("Profile extraction failed.")
