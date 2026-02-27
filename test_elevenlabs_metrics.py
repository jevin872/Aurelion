"""
ElevenLabs Testing Script for Voice Authentication System
Calculates:
- Accuracy
- False Acceptance Rate (FAR)
- False Rejection Rate (FRR)
- Equal Error Rate (EER)
"""

import sys
from pathlib import Path
import librosa
import numpy as np
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
import os
from dotenv import load_dotenv
import json
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).parent))

from backend.realtime_detector import RealtimeVoiceDetector
from backend.robust_detector import RobustVoiceDetector

load_dotenv()

# Initialize ElevenLabs
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
if not ELEVENLABS_API_KEY:
    print("ERROR: ELEVENLABS_API_KEY not found in .env file")
    sys.exit(1)

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)


def generate_ai_clone(text, output_path, voice_id="21m00Tcm4TlvDq8ikWAM"):
    """Generate AI voice clone using ElevenLabs."""
    try:
        print(f"  Generating AI clone: {output_path}")
        
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_turbo_v2_5",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True
            )
        )
        
        # Save audio
        with open(output_path, 'wb') as f:
            for chunk in audio:
                f.write(chunk)
        
        return True
    except Exception as e:
        print(f"  ERROR generating clone: {e}")
        return False


def test_voice_authentication():
    """
    Test voice authentication system with ElevenLabs AI clones.
    Calculate accuracy, FAR, FRR, and EER.
    """
    print("=" * 80)
    print("ELEVENLABS VOICE AUTHENTICATION TESTING")
    print("=" * 80)
    
    # Test configuration
    baseline_file = "dataset/real/clip_0.wav"
    test_real_files = [
        "dataset/real/clip_1.wav",
        "dataset/real/clip_2.wav",
        "dataset/real/clip_3.wav",
        "dataset/real/clip_4.wav",
        "dataset/real/clip_5.wav"
    ]
    
    # Different speakers for FAR testing
    different_speakers = []
    if Path("dataset/real/Furqanreal.wav").exists():
        different_speakers.append("dataset/real/Furqanreal.wav")
    if Path("dataset/real/HimanshuReal.wav").exists():
        different_speakers.append("dataset/real/HimanshuReal.wav")
    
    # Create output directory
    output_dir = Path("test_results/elevenlabs_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate AI clones
    print("\n" + "=" * 80)
    print("STEP 1: GENERATING AI CLONES WITH ELEVENLABS")
    print("=" * 80)
    
    test_texts = [
        "Hello, this is a test of the voice authentication system.",
        "The quick brown fox jumps over the lazy dog.",
        "Voice biometrics can identify speakers by their unique vocal characteristics.",
        "Artificial intelligence is transforming how we interact with technology.",
        "Security and privacy are essential in modern authentication systems."
    ]
    
    ai_clone_files = []
    for i, text in enumerate(test_texts):
        output_path = output_dir / f"ai_clone_{i}.wav"
        if generate_ai_clone(text, str(output_path)):
            ai_clone_files.append(str(output_path))
    
    print(f"\nGenerated {len(ai_clone_files)} AI clones")
    
    # Initialize detectors
    print("\n" + "=" * 80)
    print("STEP 2: INITIALIZING VOICE AUTHENTICATION SYSTEM")
    print("=" * 80)
    
    detector = RealtimeVoiceDetector()
    robust_detector = RobustVoiceDetector()
    
    print(f"\nSetting baseline from: {baseline_file}")
    if not detector.set_baseline(baseline_file):
        print("ERROR: Failed to set baseline")
        return
    
    baseline_features = detector.baseline_features
    robust_detector.set_baseline(baseline_features)
    print("Baseline set successfully")
    print(f"  Identity threshold: {getattr(robust_detector, 'identity_threshold', 0.95):.0%}")
    print(f"  AI detection threshold: {getattr(robust_detector, 'ai_deviation_threshold', 0.50):.0%}")
    
    # Test results storage
    results = {
        'true_positives': [],  # Real voice correctly accepted
        'false_negatives': [],  # Real voice incorrectly rejected
        'true_negatives': [],  # AI/Different speaker correctly rejected
        'false_positives': [],  # AI/Different speaker incorrectly accepted
        'scores': []  # For EER calculation
    }
    
    # Test 1: Real voice samples (same speaker) - Should ACCEPT
    print("\n" + "=" * 80)
    print("STEP 3: TESTING REAL VOICE SAMPLES (SAME SPEAKER)")
    print("=" * 80)
    print("Expected: ACCEPT (True Positive)")
    
    for i, test_file in enumerate(test_real_files, 1):
        if not Path(test_file).exists():
            continue
        
        print(f"\n[{i}/{len(test_real_files)}] Testing: {Path(test_file).name}")
        
        y, sr = librosa.load(test_file, sr=16000)
        result = detector.analyze_chunk(y, sr)
        
        if 'features' not in result:
            print("  ERROR: No features extracted")
            continue
        
        test_features = result['features']
        robust_result = robust_detector.analyze(test_features)
        
        is_match = robust_result['is_match']
        mfcc_similarity = robust_result['mfcc_similarity']
        
        print(f"  Result: {'ACCEPT' if is_match else 'REJECT'}")
        print(f"  MFCC Similarity: {mfcc_similarity:.2%}")
        
        # Store result
        if is_match:
            results['true_positives'].append({
                'file': test_file,
                'mfcc_similarity': mfcc_similarity,
                'type': 'real_same_speaker'
            })
        else:
            results['false_negatives'].append({
                'file': test_file,
                'mfcc_similarity': mfcc_similarity,
                'type': 'real_same_speaker'
            })
        
        # Store score for EER (positive class)
        results['scores'].append({
            'score': mfcc_similarity,
            'label': 1,  # Genuine
            'type': 'real_same_speaker'
        })
    
    # Test 2: Different speakers - Should REJECT
    print("\n" + "=" * 80)
    print("STEP 4: TESTING DIFFERENT SPEAKERS")
    print("=" * 80)
    print("Expected: REJECT (True Negative)")
    
    for i, test_file in enumerate(different_speakers, 1):
        print(f"\n[{i}/{len(different_speakers)}] Testing: {Path(test_file).name}")
        
        y, sr = librosa.load(test_file, sr=16000)
        result = detector.analyze_chunk(y, sr)
        
        if 'features' not in result:
            print("  ERROR: No features extracted")
            continue
        
        test_features = result['features']
        robust_result = robust_detector.analyze(test_features)
        
        is_match = robust_result['is_match']
        mfcc_similarity = robust_result['mfcc_similarity']
        
        print(f"  Result: {'ACCEPT' if is_match else 'REJECT'}")
        print(f"  MFCC Similarity: {mfcc_similarity:.2%}")
        
        # Store result
        if not is_match:
            results['true_negatives'].append({
                'file': test_file,
                'mfcc_similarity': mfcc_similarity,
                'type': 'different_speaker'
            })
        else:
            results['false_positives'].append({
                'file': test_file,
                'mfcc_similarity': mfcc_similarity,
                'type': 'different_speaker'
            })
        
        # Store score for EER (negative class)
        results['scores'].append({
            'score': mfcc_similarity,
            'label': 0,  # Impostor
            'type': 'different_speaker'
        })
    
    # Test 3: AI clones - Should REJECT
    print("\n" + "=" * 80)
    print("STEP 5: TESTING AI CLONES (ELEVENLABS)")
    print("=" * 80)
    print("Expected: REJECT (True Negative)")
    
    for i, test_file in enumerate(ai_clone_files, 1):
        print(f"\n[{i}/{len(ai_clone_files)}] Testing: {Path(test_file).name}")
        
        y, sr = librosa.load(test_file, sr=16000)
        result = detector.analyze_chunk(y, sr)
        
        if 'features' not in result:
            print("  ERROR: No features extracted")
            continue
        
        test_features = result['features']
        robust_result = robust_detector.analyze(test_features)
        
        is_match = robust_result['is_match']
        is_deepfake = robust_result.get('is_deepfake', False)
        mfcc_similarity = robust_result['mfcc_similarity']
        phase_deviation = robust_result.get('phase_deviation', 0)
        
        print(f"  Result: {'ACCEPT' if is_match else 'REJECT'}")
        print(f"  MFCC Similarity: {mfcc_similarity:.2%}")
        print(f"  Phase Deviation: {phase_deviation:.2%}")
        print(f"  Deepfake Detected: {is_deepfake}")
        
        # Store result
        if not is_match or is_deepfake:
            results['true_negatives'].append({
                'file': test_file,
                'mfcc_similarity': mfcc_similarity,
                'is_deepfake': is_deepfake,
                'type': 'ai_clone'
            })
        else:
            results['false_positives'].append({
                'file': test_file,
                'mfcc_similarity': mfcc_similarity,
                'is_deepfake': is_deepfake,
                'type': 'ai_clone'
            })
        
        # Store score for EER (negative class)
        results['scores'].append({
            'score': mfcc_similarity,
            'label': 0,  # Impostor
            'type': 'ai_clone'
        })
    
    # Calculate metrics
    print("\n" + "=" * 80)
    print("STEP 6: CALCULATING METRICS")
    print("=" * 80)
    
    tp = len(results['true_positives'])
    fn = len(results['false_negatives'])
    tn = len(results['true_negatives'])
    fp = len(results['false_positives'])
    
    total = tp + fn + tn + fp
    
    # Accuracy
    accuracy = (tp + tn) / total if total > 0 else 0
    
    # False Acceptance Rate (FAR) - Impostor accepted
    far = fp / (fp + tn) if (fp + tn) > 0 else 0
    
    # False Rejection Rate (FRR) - Genuine rejected
    frr = fn / (fn + tp) if (fn + tp) > 0 else 0
    
    # Calculate EER
    eer, eer_threshold = calculate_eer(results['scores'])
    
    print(f"\nConfusion Matrix:")
    print(f"  True Positives (TP):  {tp} - Real voice correctly accepted")
    print(f"  False Negatives (FN): {fn} - Real voice incorrectly rejected")
    print(f"  True Negatives (TN):  {tn} - Impostor correctly rejected")
    print(f"  False Positives (FP): {fp} - Impostor incorrectly accepted")
    
    print(f"\nPerformance Metrics:")
    print(f"  Accuracy:                    {accuracy:.2%}")
    print(f"  False Acceptance Rate (FAR): {far:.2%}")
    print(f"  False Rejection Rate (FRR):  {frr:.2%}")
    print(f"  Equal Error Rate (EER):      {eer:.2%}")
    print(f"  EER Threshold:               {eer_threshold:.2%}")
    
    # Detailed breakdown
    print(f"\nDetailed Breakdown:")
    print(f"  Real voice (same speaker):")
    print(f"    Accepted: {tp}/{tp+fn} ({tp/(tp+fn)*100:.1f}%)")
    print(f"    Rejected: {fn}/{tp+fn} ({fn/(tp+fn)*100:.1f}%)")
    
    impostor_total = tn + fp
    if impostor_total > 0:
        print(f"  Impostors (different speakers + AI):")
        print(f"    Rejected: {tn}/{impostor_total} ({tn/impostor_total*100:.1f}%)")
        print(f"    Accepted: {fp}/{impostor_total} ({fp/impostor_total*100:.1f}%)")
    
    # AI-specific metrics
    ai_tn = sum(1 for r in results['true_negatives'] if r['type'] == 'ai_clone')
    ai_fp = sum(1 for r in results['false_positives'] if r['type'] == 'ai_clone')
    ai_total = ai_tn + ai_fp
    
    if ai_total > 0:
        print(f"  AI Clones (ElevenLabs):")
        print(f"    Rejected: {ai_tn}/{ai_total} ({ai_tn/ai_total*100:.1f}%)")
        print(f"    Accepted: {ai_fp}/{ai_total} ({ai_fp/ai_total*100:.1f}%)")
    
    # Plot ROC curve
    plot_roc_curve(results['scores'], output_dir)
    
    # Save results
    results_file = output_dir / "test_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            'metrics': {
                'accuracy': accuracy,
                'far': far,
                'frr': frr,
                'eer': eer,
                'eer_threshold': eer_threshold
            },
            'confusion_matrix': {
                'true_positives': tp,
                'false_negatives': fn,
                'true_negatives': tn,
                'false_positives': fp
            },
            'detailed_results': {
                'true_positives': results['true_positives'],
                'false_negatives': results['false_negatives'],
                'true_negatives': results['true_negatives'],
                'false_positives': results['false_positives']
            }
        }, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if accuracy >= 0.90:
        print(f"EXCELLENT: System achieved {accuracy:.1%} accuracy")
    elif accuracy >= 0.80:
        print(f"GOOD: System achieved {accuracy:.1%} accuracy")
    elif accuracy >= 0.70:
        print(f"FAIR: System achieved {accuracy:.1%} accuracy")
    else:
        print(f"NEEDS IMPROVEMENT: System achieved {accuracy:.1%} accuracy")
    
    print(f"\nEER of {eer:.2%} indicates the system's balance between security and usability.")
    print(f"At EER threshold ({eer_threshold:.2%}), FAR and FRR are equal.")
    
    print("=" * 80)
    
    return results


def calculate_eer(scores):
    """Calculate Equal Error Rate (EER) from scores."""
    # Separate genuine and impostor scores
    genuine_scores = [s['score'] for s in scores if s['label'] == 1]
    impostor_scores = [s['score'] for s in scores if s['label'] == 0]
    
    if not genuine_scores or not impostor_scores:
        return 0.0, 0.0
    
    # Try different thresholds
    all_scores = sorted(set(genuine_scores + impostor_scores))
    
    best_eer = 1.0
    best_threshold = 0.0
    
    for threshold in all_scores:
        # FAR: Impostor accepted (score >= threshold)
        fa = sum(1 for s in impostor_scores if s >= threshold)
        far = fa / len(impostor_scores)
        
        # FRR: Genuine rejected (score < threshold)
        fr = sum(1 for s in genuine_scores if s < threshold)
        frr = fr / len(genuine_scores)
        
        # EER is where FAR = FRR
        eer = abs(far - frr)
        
        if eer < best_eer:
            best_eer = (far + frr) / 2
            best_threshold = threshold
    
    return best_eer, best_threshold


def plot_roc_curve(scores, output_dir):
    """Plot ROC curve and DET curve."""
    genuine_scores = [s['score'] for s in scores if s['label'] == 1]
    impostor_scores = [s['score'] for s in scores if s['label'] == 0]
    
    if not genuine_scores or not impostor_scores:
        return
    
    # Calculate FAR and FRR for different thresholds
    thresholds = np.linspace(0, 1, 100)
    far_list = []
    frr_list = []
    
    for threshold in thresholds:
        fa = sum(1 for s in impostor_scores if s >= threshold)
        far = fa / len(impostor_scores) if impostor_scores else 0
        
        fr = sum(1 for s in genuine_scores if s < threshold)
        frr = fr / len(genuine_scores) if genuine_scores else 0
        
        far_list.append(far)
        frr_list.append(frr)
    
    # Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # ROC Curve
    ax1.plot(far_list, [1-f for f in frr_list], 'b-', linewidth=2)
    ax1.plot([0, 1], [0, 1], 'r--', label='Random')
    ax1.set_xlabel('False Acceptance Rate (FAR)')
    ax1.set_ylabel('True Acceptance Rate (1 - FRR)')
    ax1.set_title('ROC Curve')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # DET Curve (FAR vs FRR)
    ax2.plot(far_list, frr_list, 'g-', linewidth=2)
    ax2.plot([0, 1], [1, 0], 'r--', label='Ideal')
    ax2.set_xlabel('False Acceptance Rate (FAR)')
    ax2.set_ylabel('False Rejection Rate (FRR)')
    ax2.set_title('DET Curve (FAR vs FRR)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Find EER point
    eer_idx = np.argmin(np.abs(np.array(far_list) - np.array(frr_list)))
    ax2.plot(far_list[eer_idx], frr_list[eer_idx], 'ro', markersize=10, label=f'EER: {far_list[eer_idx]:.2%}')
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig(output_dir / 'roc_det_curves.png', dpi=300, bbox_inches='tight')
    print(f"\nROC and DET curves saved to: {output_dir / 'roc_det_curves.png'}")
    plt.close()


if __name__ == "__main__":
    test_voice_authentication()
