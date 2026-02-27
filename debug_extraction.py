import sys
import traceback

sys.path.append('.')
from backend.feature_extraction_fast import extract_features

file_path = "small_data/sample_0_labelunknown.wav"

print(f"Testing extraction on {file_path}")

try:
    f = extract_features(file_path)
    if f is None:
        print("Feature extraction returned None.")
    else:
        print("Feature extraction succeeded.")
except Exception as e:
    print(f"Exception caught:")
    print(traceback.format_exc())
