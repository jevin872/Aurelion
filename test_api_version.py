import requests

API_URL = "https://polyglot-ghost-api.onrender.com"

print("Testing API version...")
print("=" * 60)

# Test 1: Health check
print("\n1. Health Check:")
try:
    r = requests.get(f"{API_URL}/health", timeout=10)
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.json()}")
except Exception as e:
    print(f"   Error: {e}")

# Test 2: Root endpoint
print("\n2. API Info:")
try:
    r = requests.get(f"{API_URL}/", timeout=10)
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.json()}")
except Exception as e:
    print(f"   Error: {e}")

# Test 3: Check if new AI detection is working
print("\n3. Testing AI Detection (upload a test file):")
print("   Upload an AI voice file to your Streamlit app to test!")
print("   If you see detailed reasons like:")
print("   'AI GENERATED VOICE DETECTED (Unnaturally smooth phase transitions, ...)'")
print("   Then the update is working! ✅")

print("\n" + "=" * 60)
print("API is responding. Check Render dashboard for deployment status.")
