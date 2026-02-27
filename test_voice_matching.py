"""
Test script to verify voice matching system works correctly.
Tests with real human voice samples from the dataset.
"""

import sys
from pathlib import Path
import librosa
import numpy as np

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from backend.realtime_detector import RealtimeVoiceDetector
from backend.robust_detector import RobustVoiceDetector

def print_separator(title=""):
    """Print a nice separator."""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)
    else:
        print()

def print_features(features, label="Features"):
    """Print key features in a readable format."""
    print(f"\n{label}:")
    print(f"  Phase Discontinuity: {features.get('phase_discontinuity_mean', 0):.4f}")
    print(f"  Spectral Centroid:   {features.get('spectral_centroid_mean', 0):.2f}")
    print(f"  Jitter:              {features.get('jitter', 0):.6f}")
    if 'mfcc_mean' in features:
        mfcc = features['mfcc_mean']
        if isinstance(mfcc, list) and len(mfcc) > 0:
            print(f"  MFCC (first 3):      [{mfcc[0]:.2f}, {mfcc[1]:.2f}, {mfcc[2]:.2f}...]")

def test_same_voice_matching():
    """Test 1: Same voice should match with high confidence."""
    print_separator("TEST 1: Same Voice Matching")
    
    # Use a real human voice sample
    test_file = "dataset/real/clip_0.wav"
    
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"📁 Using: {test_file}")
    print("🎯 Expected: MATCH with high confidence (same audio used twice)")
    
    # Initialize detectors
    detector = RealtimeVoiceDetector()
    robust_detector = RobustVoiceDetector()
    
    # Set baseline
    print("\n📝 Step 1: Setting baseline (signature)...")
    if not detector.set_baseline(test_file):
        print("❌ Failed to set baseline")
        return False
    
    baseline_features = detector.baseline_features
    robust_detector.set_baseline(baseline_features)
    print("✅ Baseline set successfully")
    print_features(baseline_features, "Baseline Features")
    
    # Test with the SAME file
    print("\n🔍 Step 2: Testing with the SAME audio file...")
    y, sr = librosa.load(test_file, sr=16000)
    result = detector.analyze_chunk(y, sr)
    
    test_features = result.get('features', {})
    print_features(test_features, "Test Features")
    
    # Robust analysis
    robust_result = robust_detector.analyze(test_features)
    
    print("\n📊 Results:")
    print(f"  Is Match:       {robust_result['is_match']}")
    print(f"  Confidence:     {robust_result['confidence']:.1%}")
    print(f"  Deviation:      {robust_result['deviation']:.1%}")
    print(f"  Threshold:      {robust_result['threshold']:.1%} ({robust_result['threshold_level']})")
    print(f"  Risk Level:     {robust_result['risk_level']}")
    print(f"  Verdict:        {robust_result['verdict']}")
    
    if 'nearly_identical' in robust_result:
        print(f"  Nearly Identical: {robust_result['nearly_identical']}")
    if 'mfcc_similarity' in robust_result:
        print(f"  MFCC Similarity:  {robust_result['mfcc_similarity']:.1%}")
    if 'phase_similarity' in robust_result:
        print(f"  Phase Similarity: {robust_result['phase_similarity']:.1%}")
    if 'spectral_similarity' in robust_result:
        print(f"  Spectral Similarity: {robust_result['spectral_similarity']:.1%}")
    
    # Verify results
    success = robust_result['is_match'] and robust_result['confidence'] > 0.8
    
    if success:
        print("\n✅ TEST PASSED: Same voice correctly matched with high confidence!")
    else:
        print("\n❌ TEST FAILED: Same voice should match with high confidence!")
        print(f"   Expected: is_match=True, confidence>80%")
        print(f"   Got: is_match={robust_result['is_match']}, confidence={robust_result['confidence']:.1%}")
    
    return success

def test_different_voice_detection():
    """Test 2: Different voices should NOT match."""
    print_separator("TEST 2: Different Voice Detection")
    
    baseline_file = "dataset/real/clip_0.wav"
    test_file = "dataset/real/clip_1.wav"
    
    if not Path(baseline_file).exists() or not Path(test_file).exists():
        print(f"❌ Test files not found")
        return False
    
    print(f"📁 Baseline: {baseline_file}")
    print(f"📁 Test:     {test_file}")
    print("🎯 Expected: NO MATCH (different speakers)")
    
    # Initialize detectors
    detector = RealtimeVoiceDetector()
    robust_detector = RobustVoiceDetector()
    
    # Set baseline
    print("\n📝 Step 1: Setting baseline...")
    detector.set_baseline(baseline_file)
    baseline_features = detector.baseline_features
    robust_detector.set_baseline(baseline_features)
    print("✅ Baseline set")
    print_features(baseline_features, "Baseline Features")
    
    # Test with different file
    print("\n🔍 Step 2: Testing with DIFFERENT audio file...")
    y, sr = librosa.load(test_file, sr=16000)
    result = detector.analyze_chunk(y, sr)
    
    test_features = result.get('features', {})
    print_features(test_features, "Test Features")
    
    # Robust analysis
    robust_result = robust_detector.analyze(test_features)
    
    print("\n📊 Results:")
    print(f"  Is Match:       {robust_result['is_match']}")
    print(f"  Confidence:     {robust_result['confidence']:.1%}")
    print(f"  Deviation:      {robust_result['deviation']:.1%}")
    print(f"  Threshold:      {robust_result['threshold']:.1%} ({robust_result['threshold_level']})")
    print(f"  Risk Level:     {robust_result['risk_level']}")
    print(f"  Verdict:        {robust_result['verdict']}")
    
    if 'mfcc_similarity' in robust_result:
        print(f"  MFCC Similarity:  {robust_result['mfcc_similarity']:.1%}")
    
    # Verify results - different voices should NOT match
    success = not robust_result['is_match']
    
    if success:
        print("\n✅ TEST PASSED: Different voices correctly identified as mismatch!")
    else:
        print("\n❌ TEST FAILED: Different voices should NOT match!")
        print(f"   Expected: is_match=False")
        print(f"   Got: is_match={robust_result['is_match']}")
    
    return success

def test_ai_voice_detection():
    """Test 3: AI-generated voices should be detected."""
    print_separator("TEST 3: AI Voice Detection")
    
    baseline_file = "dataset/real/clip_0.wav"
    test_file = "dataset/fake/Ali.wav"
    
    if not Path(baseline_file).exists() or not Path(test_file).exists():
        print(f"❌ Test files not found")
        return False
    
    print(f"📁 Baseline (Real): {baseline_file}")
    print(f"📁 Test (AI):       {test_file}")
    print("🎯 Expected: AI DETECTED or MISMATCH")
    
    # Initialize detectors
    detector = RealtimeVoiceDetector()
    robust_detector = RobustVoiceDetector()
    
    # Set baseline
    print("\n📝 Step 1: Setting baseline (real voice)...")
    detector.set_baseline(baseline_file)
    baseline_features = detector.baseline_features
    robust_detector.set_baseline(baseline_features)
    print("✅ Baseline set")
    print_features(baseline_features, "Baseline Features (Real)")
    
    # Test with AI voice
    print("\n🔍 Step 2: Testing with AI-generated voice...")
    y, sr = librosa.load(test_file, sr=16000)
    result = detector.analyze_chunk(y, sr)
    
    test_features = result.get('features', {})
    print_features(test_features, "Test Features (AI)")
    
    # Robust analysis
    robust_result = robust_detector.analyze(test_features)
    
    print("\n📊 Results:")
    print(f"  Is Match:       {robust_result['is_match']}")
    print(f"  Is AI Generated: {robust_result.get('is_ai_generated', False)}")
    print(f"  Confidence:     {robust_result['confidence']:.1%}")
    print(f"  Deviation:      {robust_result['deviation']:.1%}")
    print(f"  Risk Level:     {robust_result['risk_level']}")
    print(f"  Verdict:        {robust_result['verdict']}")
    
    if 'mfcc_similarity' in robust_result:
        print(f"  MFCC Similarity:  {robust_result['mfcc_similarity']:.1%}")
    
    # Verify results - AI voice should be detected or not match
    success = not robust_result['is_match'] or robust_result.get('is_ai_generated', False)
    
    if success:
        print("\n✅ TEST PASSED: AI voice correctly detected or rejected!")
    else:
        print("\n❌ TEST FAILED: AI voice should be detected or not match!")
        print(f"   Expected: is_match=False OR is_ai_generated=True")
        print(f"   Got: is_match={robust_result['is_match']}, is_ai_generated={robust_result.get('is_ai_generated', False)}")
    
    return success

def main():
    """Run all tests."""
    print_separator("🧪 VOICE MATCHING SYSTEM TEST SUITE")
    print("\nTesting the voice authentication system with real audio samples...")
    print("This will verify that:")
    print("  1. Same voice matches with high confidence")
    print("  2. Different voices are correctly rejected")
    print("  3. AI-generated voices are detected")
    
    results = []
    
    # Test 1: Same voice
    try:
        results.append(("Same Voice Matching", test_same_voice_matching()))
    except Exception as e:
        print(f"\n❌ Test 1 crashed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Same Voice Matching", False))
    
    # Test 2: Different voices
    try:
        results.append(("Different Voice Detection", test_different_voice_detection()))
    except Exception as e:
        print(f"\n❌ Test 2 crashed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Different Voice Detection", False))
    
    # Test 3: AI detection
    try:
        results.append(("AI Voice Detection", test_ai_voice_detection()))
    except Exception as e:
        print(f"\n❌ Test 3 crashed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("AI Voice Detection", False))
    
    # Summary
    print_separator("📋 TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status}: {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is working correctly!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. System needs adjustment.")
    
    print_separator()

if __name__ == "__main__":
    main()
