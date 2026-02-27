import os
import streamlit as st
import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.dl_extractor import KuralPulseExtractor
from backend.auth_engine import KuralPulseAuthEngine
from backend.api_integrations import APIIntegrations

st.set_page_config(page_title="Kural-Pulse Bank Auth", layout="wide", page_icon="🔐")

# Initialize models
@st.cache_resource
def load_models():
    return KuralPulseExtractor()

with st.spinner("Loading Kural-Pulse Deep Learning Models (SpeechBrain & Wav2Vec 2.0)..."):
    extractor = load_models()

if 'auth_engine' not in st.session_state:
    st.session_state.auth_engine = KuralPulseAuthEngine()
if 'api' not in st.session_state:
    st.session_state.api = APIIntegrations()

st.title("🛡️ Kural-Pulse: Voice Biometric & Anti-Spoofing")
st.markdown("Advanced Banking Security via Deep Speaker Embeddings & Generative Artifact Detection")

def plot_spectrogram(y, sr):
    fig, ax = plt.subplots(figsize=(10, 4))
    D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
    img = librosa.display.specshow(D, y_axis='hz', x_axis='time', sr=sr, ax=ax)
    fig.colorbar(img, ax=ax, format="%+2.0f dB")
    ax.set_title('Live Spectrogram')
    return fig

# UI TABS
tab1, tab2, tab3 = st.tabs(["🔒 1. Enroll Signature", "🎙️ 2. Live Authentication", "👻 3. Attack Simulation"])

# TAB 1: ENROLLMENT
with tab1:
    st.header("Step 1: Biological Enrollment")
    st.markdown("Capture 10+ seconds of your raw voice to establish your 'Vocal Twin'.")
    enroll_audio = st.audio_input("Record your Baseline Phrase")
    
    if enroll_audio:
        if st.button("Extract Deep Signature"):
            with open("temp_enroll.wav", "wb") as f:
                f.write(enroll_audio.getbuffer())
            with st.spinner("Extracting Biological Blueprint (SpeechBrain)..."):
                profile = extractor.get_full_profile("temp_enroll.wav")
                if profile and st.session_state.auth_engine.set_vocal_twin(profile):
                    st.success("✅ **Signature securely hashed and stored!** You are now enrolled.")
                    st.json({"identity_vector_length": len(profile['identity_embedding'])})
                else:
                    st.error("Enrollment failed. Audio may be too short or completely silent.")

# TAB 2: VERIFICATION
with tab2:
    st.header("Step 2: Real-time Multi-Factor Authentication")
    
    if not st.session_state.auth_engine.baseline_profile:
        st.warning("⚠️ Please enroll a Signature in Step 1 first.")
    else:
        test_audio = st.audio_input("Speak to Authenticate")
        if test_audio:
            if st.button("Authenticate Identity"):
                with open("temp_test.wav", "wb") as f:
                    f.write(test_audio.getbuffer())
                    
                with st.spinner("Analyzing Spectral Stitches & Extracting Identity..."):
                    # Render Spectrogram
                    y, sr = librosa.load("temp_test.wav", sr=16000)
                    st.pyplot(plot_spectrogram(y, sr))
                    
                    test_profile = extractor.get_full_profile("temp_test.wav")
                    
                    if test_profile:
                        # Auth Logic
                        result = st.session_state.auth_engine.verify(test_profile)
                        
                        col1, col2 = st.columns(2)
                        
                        # Column 1: Match score
                        match_pct = result['identity_match_score']
                        col1.metric("🧬 Identity Match", f"{match_pct:.2f}%", delta=f"{match_pct-85:.2f}% from Threshold", delta_color="normal" if match_pct >= 85 else "inverse")
                        
                        # Column 2: AI score
                        ai_pct = result['ai_probability_score']
                        col2.metric("👻 AI Deepfake Risk", f"{ai_pct:.2f}%", delta=f"{ai_pct-70:.2f}% from Threshold", delta_color="inverse" if ai_pct >= 70 else "normal")
                        
                        st.divider()
                        
                        # Verdict rendering
                        if result["passed"]:
                            st.success(f"### ✅ {result['verdict']}\n{result['reason']}")
                        else:
                            st.error(f"### 🛑 {result['verdict']}\n{result['reason']}")
                            
                            # Cognitive Liveness hook
                            if result.get("requires_liveness"):
                                st.warning("⚠️ Borderline AI Artifacts Detected. Triggering Dynamic Cognitive Liveness Challenge...")
                                challenge = st.session_state.api.cognitive_liveness_challenge()
                                st.info(f"**Featherless AI Says:** Please repeat the following phrase exactly to prove liveness:\n\n> {challenge}")

# TAB 3: ATTACK SIMULATION
with tab3:
    st.header("Step 3: Synthetic Ghost Attack (ElevenLabs)")
    st.markdown("Use this to generate a synthetic voice clone and bypass the system. We will see if the Deepfake engine catches it.")
    
    attack_text = st.text_area("Attack Phrase:", "Hello, I am the account owner. My voice is my password. Authorize my transaction.")
    
    if st.button("Generate & Launch ElevenLabs Attack"):
        with st.spinner("Calling ElevenLabs to generate synthetic clone..."):
            success = st.session_state.api.generate_attack_sample(text=attack_text, output_path="temp_attack.wav")
            if success:
                st.audio("temp_attack.wav")
                st.success("Attack Generated. Now evaluating it against Kural-Pulse...")
                
                with st.spinner("Deepfake Analysis..."):
                    attack_profile = extractor.get_full_profile("temp_attack.wav")
                    if attack_profile:
                        # Since this Elevenlabs voice isn't ACTUALLY the user's voice, the identity will fail.
                        # But we specifically want to see if the AI probability is caught.
                        ai_pct = st.session_state.auth_engine.is_ai_probability(attack_profile.get("artifacts", {})) * 100
                        st.metric("Ghost Detection (AI Risk)", f"{ai_pct:.2f}%")
                        if ai_pct >= 70.0:
                            st.error("🛑 ATTACK BLOCKED - Kural-Pulse intercepted the Deepfake.")
                        else:
                            st.warning("⚠️ ATTACK BYPASSED - System did not flag as AI (though identity might still block).")
            else:
                st.error("ElevenLabs API call failed. Check your API key or limits.")
