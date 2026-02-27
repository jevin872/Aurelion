import os
import requests
from dotenv import load_dotenv

load_dotenv()

class APIIntegrations:
    def __init__(self):
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.featherless_api_key = os.getenv("FEATHERLESS_API_KEY")
        self.featherless_base_url = os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1")
        
    def generate_attack_sample(self, text="Hello, my voice is my password. Authenticate me immediately.", output_path="synthetic_attack.wav"):
        """
        Uses ElevenLabs to generate a synthetic clone.
        Note: You'll typically need a pre-cloned 'voice_id'. 
        For demonstration without a specific ID, we use a generic default high-quality voice
        which simulates a 'Ghost Attack' in spectral properties.
        """
        if not self.elevenlabs_api_key:
            print("Missing ElevenLabs API Key.")
            return False
            
        url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM" # Generic voice for demo
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        try:
            print(f"Generating ElevenLabs attack sample...")
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                # Save as MP3 temporarily, then pydub will handle it in the extractor
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"Attack sample saved to {output_path}")
                return True
            else:
                print(f"ElevenLabs error: {response.status_code}")
                return False
        except Exception as e:
            print(f"ElevenLabs request failed: {e}")
            return False

    def cognitive_liveness_challenge(self):
        """
        Calls Featherless AI to generate a dynamic, unpredictable challenge phrase 
        that a pre-recorded Deepfake wouldn't be able to predict.
        """
        if not self.featherless_api_key:
            return "Please repeat the following phrase: 'The quick brown fox jumps over the lazy dog.'"
            
        try:
            from openai import OpenAI
            client = OpenAI(
                base_url=self.featherless_base_url,
                api_key=self.featherless_api_key
            )
            
            response = client.chat.completions.create(
                model="meta-llama/Meta-Llama-3-8B-Instruct", # Example model, or whichever featherless is serving
                messages=[
                    {"role": "system", "content": "You are a voice biometrics security system. Generate a short, completely random 5-10 word tongue twister or absurd sentence that the user must repeat exactly to prove liveness. Output only the sentence."},
                    {"role": "user", "content": "Generate challenge."}
                ],
                max_tokens=30,
                temperature=0.9
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Featherless AI error: {e}")
            return "Server error. Please repeat: 'Blue rubber baby buggy bumpers'."
