import json
import os
import numpy as np

def build_simple_classifier(features_file="features.json", output_file="classifier_params.json"):
    """
    Builds a simple threshold-based classifier for AI detection based on Phase Discontinuity.
    This reads from features.json and generates classifier_params.json.
    """
    if not os.path.exists(features_file):
        print(f"Error: Features file {features_file} not found.")
        return False
        
    try:
        with open(features_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading {features_file}: {e}")
        return False

    if not data:
        print("Data is empty.")
        return False

    # Extract phase discontinuities
    discontinuities = []
    
    for filename, feats in data.items():
        if "phase_discontinuity_mean" in feats:
            discontinuities.append(feats["phase_discontinuity_mean"])
            
    if not discontinuities:
        print("Error: No phase discontinuity features found in the dataset.")
        return False
        
    # Calculate statistics
    mean_disc = np.mean(discontinuities)
    std_disc = np.std(discontinuities)
    
    # We set a slightly hardcoded safe threshold based on the VOICE_MATCHING_ANALYSIS.md
    # where it recommended 2.15 to avoid false positives. 
    # But if the dataset has a higher baseline, we'll bump it slightly.
    base_threshold = max(2.15, mean_disc + (3 * std_disc))
    
    params = {
        "type": "threshold",
        "feature": "phase_discontinuity_mean",
        "threshold": float(base_threshold),
        "mean": float(mean_disc),
        "std": float(std_disc),
        "comment": "Threshold set to identify Phase Discontinuities associated with AI generated audio."
    }
    
    with open(output_file, 'w') as f:
        json.dump(params, f, indent=4)
        
    print(f"✅ Trained model successfully! Phase threshold is {base_threshold:.3f}")
    return True
