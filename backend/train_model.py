import os
import json
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import time

# Load environment variables
load_dotenv()

# Initialize Featherless client
client = OpenAI(
    api_key=os.getenv("FEATHERLESS_API_KEY"),
    base_url=os.getenv("FEATHERLESS_BASE_URL")
)


def flatten_features(feature_dict):
    """
    Flatten nested feature dictionary into a single vector.
    
    Args:
        feature_dict: Dictionary with features
    
    Returns:
        Flattened numpy array
    """
    flat_features = []
    
    for key, value in feature_dict.items():
        if key in ['filename', 'label']:
            continue
        
        if isinstance(value, list):
            flat_features.extend(value)
        else:
            flat_features.append(value)
    
    return np.array(flat_features)


def prepare_training_data(features_file='features.json'):
    """
    Prepare training data from extracted features.
    
    Args:
        features_file: Path to features JSON file
    
    Returns:
        Tuple of (X, y, feature_names)
    """
    with open(features_file, 'r') as f:
        dataset = json.load(f)
    
    X = []
    y = []
    filenames = []
    
    for sample in dataset:
        features = flatten_features(sample)
        X.append(features)
        
        # Label: 0 for real, 1 for fake/AI-generated
        # Since labels are unknown, we'll need to manually label or use unsupervised
        label = sample.get('label')
        y.append(label)
        filenames.append(sample['filename'])
    
    X = np.array(X)
    y = np.array(y)
    
    print(f"Feature matrix shape: {X.shape}")
    print(f"Labels shape: {y.shape}")
    print(f"Unique labels: {np.unique(y)}")
    
    return X, y, filenames


def create_training_prompt(X, y, filenames):
    """
    Create a training prompt for the Featherless API.
    
    Args:
        X: Feature matrix
        y: Labels
        filenames: List of filenames
    
    Returns:
        Training prompt string
    """
    # Create a summary of the dataset
    prompt = f"""You are an AI voice detection expert. I have extracted audio features from {len(X)} voice samples to train a classifier that detects AI-generated voices.

Features extracted per sample:
- MFCC (Mel-Frequency Cepstral Coefficients): 40 coefficients + statistics
- STFT (Short-Time Fourier Transform) features: spectral centroid, rolloff, bandwidth, contrast
- Phase Continuity features: phase discontinuity metrics, unwrapped phase analysis

Total features per sample: {X.shape[1]}

Dataset statistics:
- Mean feature values: {np.mean(X, axis=0)[:10].tolist()} (first 10)
- Std feature values: {np.std(X, axis=0)[:10].tolist()} (first 10)
- Feature range: [{np.min(X):.4f}, {np.max(X):.4f}]

Sample data (first 3 samples):
"""
    
    for i in range(min(3, len(X))):
        prompt += f"\nSample {i+1} ({filenames[i]}):\n"
        prompt += f"  Features (first 20): {X[i][:20].tolist()}\n"
        prompt += f"  Label: {y[i]}\n"
    
    prompt += """

Based on these features, please provide:
1. Analysis of which features are most discriminative for detecting AI-generated voices
2. Recommended classification approach (threshold-based, ML model, etc.)
3. Feature importance insights
4. Suggestions for improving detection accuracy
"""
    
    return prompt


def train_with_featherless(features_file='features.json', model='meta-llama/Meta-Llama-3.1-70B-Instruct'):
    """
    Train/analyze the model using Featherless API.
    
    Args:
        features_file: Path to features JSON file
        model: Model to use on Featherless
    
    Returns:
        API response with analysis
    """
    print("Loading features...")
    X, y, filenames = prepare_training_data(features_file)
    
    print("\nCreating training prompt...")
    prompt = create_training_prompt(X, y, filenames)
    
    print(f"\nSending request to Featherless API (model: {model})...")
    print("This may take a moment...\n")
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in audio signal processing and AI-generated voice detection. Analyze audio features and provide insights for building a classifier."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        analysis = response.choices[0].message.content
        
        print("=" * 80)
        print("FEATHERLESS API ANALYSIS")
        print("=" * 80)
        print(analysis)
        print("=" * 80)
        
        # Save analysis
        output_file = 'model_analysis.txt'
        with open(output_file, 'w') as f:
            f.write(f"Model: {model}\n")
            f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Dataset size: {len(X)} samples\n")
            f.write(f"Feature dimensions: {X.shape[1]}\n")
            f.write("\n" + "=" * 80 + "\n")
            f.write(analysis)
        
        print(f"\nAnalysis saved to {output_file}")
        
        return analysis
        
    except Exception as e:
        print(f"Error calling Featherless API: {e}")
        return None


def build_simple_classifier(features_file='features.json'):
    """
    Build a simple threshold-based classifier using phase continuity.
    This serves as a baseline model.
    
    Args:
        features_file: Path to features JSON file
    
    Returns:
        Classifier parameters
    """
    with open(features_file, 'r') as f:
        dataset = json.load(f)
    
    phase_discontinuities = []
    
    for sample in dataset:
        phase_disc = sample.get('phase_discontinuity_mean', 0)
        phase_discontinuities.append(phase_disc)
    
    phase_discontinuities = np.array(phase_discontinuities)
    
    # Calculate threshold (mean + 1 std)
    threshold = np.mean(phase_discontinuities) + np.std(phase_discontinuities)
    
    print(f"\nSimple Classifier (Phase Discontinuity):")
    print(f"  Mean: {np.mean(phase_discontinuities):.6f}")
    print(f"  Std: {np.std(phase_discontinuities):.6f}")
    print(f"  Threshold: {threshold:.6f}")
    print(f"  Samples above threshold: {np.sum(phase_discontinuities > threshold)}")
    
    # Save classifier
    classifier_params = {
        'type': 'threshold',
        'feature': 'phase_discontinuity_mean',
        'threshold': float(threshold),
        'mean': float(np.mean(phase_discontinuities)),
        'std': float(np.std(phase_discontinuities))
    }
    
    with open('classifier_params.json', 'w') as f:
        json.dump(classifier_params, f, indent=2)
    
    print(f"\nClassifier parameters saved to classifier_params.json")
    
    return classifier_params


if __name__ == "__main__":
    print("=" * 80)
    print("AI VOICE DETECTION - TRAINING PIPELINE")
    print("=" * 80)
    
    # Check if features exist
    if not Path('features.json').exists():
        print("\nFeatures file not found. Please run feature_extraction.py first.")
        exit(1)
    
    # Build simple classifier
    print("\n1. Building simple baseline classifier...")
    classifier_params = build_simple_classifier()
    
    # Get AI analysis from Featherless
    print("\n2. Getting AI analysis from Featherless API...")
    analysis = train_with_featherless()
    
    print("\n" + "=" * 80)
    print("TRAINING COMPLETE")
    print("=" * 80)
