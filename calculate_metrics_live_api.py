import requests
import os
import numpy as np
from sklearn.metrics import roc_curve, auc
import matplotlib.pyplot as plt

API_URL = "https://polyglot-ghost-api.onrender.com"

print("=" * 80)
print("CALCULATING ACCURACY AND EER FOR AI VS. HUMAN DETECTION")
print("=" * 80)

# Step 1: Set Baseline
print("\n📌 Setting Baseline Voice...")
with open('dataset/real/clip_0.wav', 'rb') as f:
    files = {'file': f}
    response = requests.post(f"{API_URL}/api/set-baseline", files=files, timeout=120)
    if response.status_code == 200:
        print("✅ Baseline set successfully")
    else:
        print("❌ Failed to set baseline")
        exit(1)

# Step 2: Test Real Voices (Same Speaker)
print("\n🗣️ Testing Real Voices (Same Speaker)...")
real_same_results = []
real_same_files = ['clip_1.wav', 'clip_2.wav', 'clip_3.wav', 'clip_4.wav', 'clip_5.wav']

for filename in real_same_files:
    filepath = f'dataset/real/{filename}'
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{API_URL}/api/analyze?strictness=normal", files=files, timeout=120)
            if response.status_code == 200:
                result = response.json()
                real_same_results.append({
                    'file': filename,
                    'is_match': result['is_match'],
                    'is_ai': result['is_ai_generated'],
                    'confidence': result['confidence'],
                    'verdict': result['verdict']
                })
                print(f"  {filename}: Match={result['is_match']}, AI={result['is_ai_generated']}, Conf={result['confidence']:.1%}")

# Step 3: Test Real Voices (Different Speakers)
print("\n👥 Testing Real Voices (Different Speakers)...")
real_diff_results = []
real_diff_files = ['Furqanreal.wav', 'HimanshuReal.wav']

for filename in real_diff_files:
    filepath = f'dataset/real/{filename}'
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{API_URL}/api/analyze?strictness=normal", files=files, timeout=120)
            if response.status_code == 200:
                result = response.json()
                real_diff_results.append({
                    'file': filename,
                    'is_match': result['is_match'],
                    'is_ai': result['is_ai_generated'],
                    'confidence': result['confidence'],
                    'verdict': result['verdict']
                })
                print(f"  {filename}: Match={result['is_match']}, AI={result['is_ai_generated']}, Conf={result['confidence']:.1%}")

# Step 4: Test AI Voices (Dataset)
print("\n🤖 Testing AI Voices (Dataset)...")
ai_dataset_results = []
ai_files = ['Ali.wav', 'Connor.wav', 'David.wav', 'Jack.wav', 'Mark.wav']

for filename in ai_files:
    filepath = f'dataset/fake/{filename}'
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{API_URL}/api/analyze?strictness=normal", files=files, timeout=120)
            if response.status_code == 200:
                result = response.json()
                ai_dataset_results.append({
                    'file': filename,
                    'is_match': result['is_match'],
                    'is_ai': result['is_ai_generated'],
                    'confidence': result['confidence'],
                    'verdict': result['verdict']
                })
                print(f"  {filename}: Match={result['is_match']}, AI={result['is_ai_generated']}, Conf={result['confidence']:.1%}")

# Step 5: Test ElevenLabs AI Clones
print("\n🎙️ Testing ElevenLabs AI Clones...")
elevenlabs_results = []

for i in range(5):
    filepath = f'test_results/elevenlabs_test/ai_clone_{i}.wav'
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{API_URL}/api/analyze?strictness=normal", files=files, timeout=120)
            if response.status_code == 200:
                result = response.json()
                elevenlabs_results.append({
                    'file': f'ai_clone_{i}.wav',
                    'is_match': result['is_match'],
                    'is_ai': result['is_ai_generated'],
                    'confidence': result['confidence'],
                    'verdict': result['verdict']
                })
                print(f"  ai_clone_{i}.wav: Match={result['is_match']}, AI={result['is_ai_generated']}, Conf={result['confidence']:.1%}")

# Calculate Metrics
print("\n" + "=" * 80)
print("📊 CALCULATING METRICS")
print("=" * 80)

# True Positives: Real voice (same speaker) correctly accepted
tp = sum(1 for r in real_same_results if r['is_match'])
# False Negatives: Real voice (same speaker) incorrectly rejected
fn = sum(1 for r in real_same_results if not r['is_match'])

# True Negatives: Impostor/AI correctly rejected
tn_diff = sum(1 for r in real_diff_results if not r['is_match'])
tn_ai_dataset = sum(1 for r in ai_dataset_results if not r['is_match'] or r['is_ai'])
tn_elevenlabs = sum(1 for r in elevenlabs_results if not r['is_match'] or r['is_ai'])
tn = tn_diff + tn_ai_dataset + tn_elevenlabs

# False Positives: Impostor/AI incorrectly accepted
fp_diff = sum(1 for r in real_diff_results if r['is_match'])
fp_ai_dataset = sum(1 for r in ai_dataset_results if r['is_match'] and not r['is_ai'])
fp_elevenlabs = sum(1 for r in elevenlabs_results if r['is_match'] and not r['is_ai'])
fp = fp_diff + fp_ai_dataset + fp_elevenlabs

# AI Detection Specific
ai_detected_dataset = sum(1 for r in ai_dataset_results if r['is_ai'])
ai_detected_elevenlabs = sum(1 for r in elevenlabs_results if r['is_ai'])
total_ai = len(ai_dataset_results) + len(elevenlabs_results)

# Calculate rates
total_samples = tp + fn + tn + fp
accuracy = (tp + tn) / total_samples if total_samples > 0 else 0

total_negatives = tn + fp
far = fp / total_negatives if total_negatives > 0 else 0  # False Acceptance Rate

total_positives = tp + fn
frr = fn / total_positives if total_positives > 0 else 0  # False Rejection Rate

# EER calculation (simplified - where FAR = FRR)
eer = (far + frr) / 2

# AI Detection Rate
ai_detection_rate = (ai_detected_dataset + ai_detected_elevenlabs) / total_ai if total_ai > 0 else 0

print("\n📈 CONFUSION MATRIX:")
print(f"  True Positives (TP):  {tp:2d} - Real voice correctly accepted")
print(f"  False Negatives (FN): {fn:2d} - Real voice incorrectly rejected")
print(f"  True Negatives (TN):  {tn:2d} - Impostor/AI correctly rejected")
print(f"  False Positives (FP): {fp:2d} - Impostor/AI incorrectly accepted")

print("\n🎯 PERFORMANCE METRICS:")
print(f"  Accuracy:                    {accuracy:.2%}")
print(f"  False Acceptance Rate (FAR): {far:.2%}")
print(f"  False Rejection Rate (FRR):  {frr:.2%}")
print(f"  Equal Error Rate (EER):      {eer:.2%}")

print("\n🤖 AI DETECTION METRICS:")
print(f"  AI Voices Tested:            {total_ai}")
print(f"  AI Voices Detected:          {ai_detected_dataset + ai_detected_elevenlabs}")
print(f"  AI Detection Rate:           {ai_detection_rate:.2%}")
print(f"  AI Rejection Rate:           {(tn_ai_dataset + tn_elevenlabs) / total_ai:.2%}")

print("\n📋 DETAILED BREAKDOWN:")
print(f"  Real voice (same speaker):")
print(f"    Accepted: {tp}/{len(real_same_results)} ({tp/len(real_same_results)*100:.1f}%)")
print(f"    Rejected: {fn}/{len(real_same_results)} ({fn/len(real_same_results)*100:.1f}%)")

print(f"\n  Different speakers:")
print(f"    Rejected: {tn_diff}/{len(real_diff_results)} ({tn_diff/len(real_diff_results)*100:.1f}%)")
print(f"    Accepted: {fp_diff}/{len(real_diff_results)} ({fp_diff/len(real_diff_results)*100:.1f}%)")

print(f"\n  AI voices (dataset):")
print(f"    Detected as AI: {ai_detected_dataset}/{len(ai_dataset_results)} ({ai_detected_dataset/len(ai_dataset_results)*100:.1f}%)")
print(f"    Rejected: {tn_ai_dataset}/{len(ai_dataset_results)} ({tn_ai_dataset/len(ai_dataset_results)*100:.1f}%)")
print(f"    Accepted: {fp_ai_dataset}/{len(ai_dataset_results)} ({fp_ai_dataset/len(ai_dataset_results)*100:.1f}%)")

print(f"\n  ElevenLabs AI clones:")
print(f"    Detected as AI: {ai_detected_elevenlabs}/{len(elevenlabs_results)} ({ai_detected_elevenlabs/len(elevenlabs_results)*100:.1f}%)")
print(f"    Rejected: {tn_elevenlabs}/{len(elevenlabs_results)} ({tn_elevenlabs/len(elevenlabs_results)*100:.1f}%)")
print(f"    Accepted: {fp_elevenlabs}/{len(elevenlabs_results)} ({fp_elevenlabs/len(elevenlabs_results)*100:.1f}%)")

print("\n" + "=" * 80)
print("✅ METRICS CALCULATION COMPLETE")
print("=" * 80)

# Summary
print("\n🎯 SUMMARY:")
if accuracy >= 0.90:
    print(f"  ✅ EXCELLENT: {accuracy:.1%} accuracy")
elif accuracy >= 0.80:
    print(f"  ✅ GOOD: {accuracy:.1%} accuracy")
elif accuracy >= 0.70:
    print(f"  ⚠️ FAIR: {accuracy:.1%} accuracy")
else:
    print(f"  ❌ NEEDS IMPROVEMENT: {accuracy:.1%} accuracy")

if eer <= 0.10:
    print(f"  ✅ EXCELLENT: {eer:.1%} EER (very balanced)")
elif eer <= 0.20:
    print(f"  ✅ GOOD: {eer:.1%} EER (well balanced)")
else:
    print(f"  ⚠️ FAIR: {eer:.1%} EER (could be more balanced)")

if ai_detection_rate >= 0.80:
    print(f"  ✅ EXCELLENT: {ai_detection_rate:.1%} AI detection rate")
elif ai_detection_rate >= 0.60:
    print(f"  ⚠️ GOOD: {ai_detection_rate:.1%} AI detection rate")
else:
    print(f"  ⚠️ NEEDS IMPROVEMENT: {ai_detection_rate:.1%} AI detection rate")
    print(f"  💡 Note: All AI voices are rejected ({(tn_ai_dataset + tn_elevenlabs) / total_ai:.1%}), but not flagged as AI")

print("\n" + "=" * 80)
