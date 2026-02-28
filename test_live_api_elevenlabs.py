import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://polyglot-ghost-api.onrender.com"

print("=" * 80)
print("TESTING LIVE API WITH ELEVENLABS AI VOICES")
print("=" * 80)

# Test 1: Set Baseline with Real Voice
print("\n1. Setting Baseline (Real Voice)")
print("   File: dataset/real/clip_0.wav")

with open('dataset/real/clip_0.wav', 'rb') as f:
    files = {'file': f}
    try:
        response = requests.post(f"{API_URL}/api/set-baseline", files=files, timeout=120)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ {response.json()['message']}")
        else:
            print(f"   ❌ Error: {response.json()}")
    except requests.Timeout:
        print("   ⏱️ Timeout - Backend may be cold starting. Wait 30s and try again.")
        exit(1)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        exit(1)

# Test 2: Test with Same Real Voice
print("\n2. Testing Same Voice (Should ACCEPT)")
print("   File: dataset/real/clip_1.wav")

with open('dataset/real/clip_1.wav', 'rb') as f:
    files = {'file': f}
    response = requests.post(f"{API_URL}/api/analyze?strictness=normal", files=files, timeout=120)
    result = response.json()
    
    print(f"   Status: {response.status_code}")
    print(f"   Is Match: {result['is_match']}")
    print(f"   Is AI: {result['is_ai_generated']}")
    print(f"   Verdict: {result['verdict']}")
    print(f"   Confidence: {result['confidence']:.1%}")
    
    if result['is_match'] and not result['is_ai_generated']:
        print("   ✅ PASSED - Correctly accepted same voice")
    else:
        print("   ⚠️ FAILED - Should have accepted")

# Test 3: Test with Different Real Voice
print("\n3. Testing Different Voice (Should REJECT)")
print("   File: dataset/real/Furqanreal.wav")

with open('dataset/real/Furqanreal.wav', 'rb') as f:
    files = {'file': f}
    response = requests.post(f"{API_URL}/api/analyze?strictness=normal", files=files, timeout=120)
    result = response.json()
    
    print(f"   Status: {response.status_code}")
    print(f"   Is Match: {result['is_match']}")
    print(f"   Is AI: {result['is_ai_generated']}")
    print(f"   Verdict: {result['verdict']}")
    print(f"   Confidence: {result['confidence']:.1%}")
    
    if not result['is_match']:
        print("   ✅ PASSED - Correctly rejected different voice")
    else:
        print("   ⚠️ FAILED - Should have rejected")

# Test 4: Test with AI Voice from Dataset
print("\n4. Testing AI Voice from Dataset (Should DETECT AI)")
print("   File: dataset/fake/Ali.wav")

with open('dataset/fake/Ali.wav', 'rb') as f:
    files = {'file': f}
    response = requests.post(f"{API_URL}/api/analyze?strictness=normal", files=files, timeout=120)
    result = response.json()
    
    print(f"   Status: {response.status_code}")
    print(f"   Is Match: {result['is_match']}")
    print(f"   Is AI: {result['is_ai_generated']}")
    print(f"   Verdict: {result['verdict']}")
    print(f"   Confidence: {result['confidence']:.1%}")
    
    if result['is_ai_generated'] or not result['is_match']:
        print("   ✅ PASSED - Correctly detected/rejected AI voice")
    else:
        print("   ⚠️ FAILED - Should have detected AI")

# Test 5: Test with ElevenLabs AI Clone
print("\n5. Testing ElevenLabs AI Clone (Should DETECT AI)")
print("   File: test_results/elevenlabs_test/ai_clone_0.wav")

if os.path.exists('test_results/elevenlabs_test/ai_clone_0.wav'):
    with open('test_results/elevenlabs_test/ai_clone_0.wav', 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{API_URL}/api/analyze?strictness=normal", files=files, timeout=120)
        result = response.json()
        
        print(f"   Status: {response.status_code}")
        print(f"   Is Match: {result['is_match']}")
        print(f"   Is AI: {result['is_ai_generated']}")
        print(f"   Verdict: {result['verdict']}")
        print(f"   Confidence: {result['confidence']:.1%}")
        print(f"   MFCC Similarity: {result['mfcc_similarity']:.1%}")
        
        if result['is_ai_generated']:
            print("   ✅ PASSED - AI DETECTED!")
            print(f"   🎯 Detection Method: {result['verdict']}")
        elif not result['is_match']:
            print("   ⚠️ PARTIAL - Rejected but not flagged as AI")
        else:
            print("   ❌ FAILED - Should have detected AI")
else:
    print("   ⚠️ SKIPPED - ElevenLabs test file not found")

# Test 6: Test Multiple ElevenLabs Clones
print("\n6. Testing Multiple ElevenLabs AI Clones")

ai_detected = 0
total_clones = 0

for i in range(5):
    clone_file = f'test_results/elevenlabs_test/ai_clone_{i}.wav'
    if os.path.exists(clone_file):
        total_clones += 1
        with open(clone_file, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{API_URL}/api/analyze?strictness=normal", files=files, timeout=120)
            result = response.json()
            
            if result['is_ai_generated']:
                ai_detected += 1
                print(f"   Clone {i}: ✅ AI DETECTED - {result['verdict'][:50]}...")
            elif not result['is_match']:
                print(f"   Clone {i}: ⚠️ REJECTED (not flagged as AI)")
            else:
                print(f"   Clone {i}: ❌ ACCEPTED (should detect AI)")

if total_clones > 0:
    detection_rate = (ai_detected / total_clones) * 100
    print(f"\n   AI Detection Rate: {ai_detected}/{total_clones} ({detection_rate:.1f}%)")
    
    if detection_rate >= 80:
        print("   ✅ EXCELLENT - High AI detection rate!")
    elif detection_rate >= 60:
        print("   ⚠️ GOOD - Decent AI detection")
    else:
        print("   ❌ NEEDS IMPROVEMENT - Low AI detection rate")
else:
    print("   ⚠️ No ElevenLabs clones found for testing")

print("\n" + "=" * 80)
print("TESTING COMPLETE")
print("=" * 80)
