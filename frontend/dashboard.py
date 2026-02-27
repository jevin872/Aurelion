import os
import streamlit as st
import librosa
import numpy as np

# Add backend to path logic if needed
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.realtime_detector import RealtimeVoiceDetector
from backend.robust_detector import RobustVoiceDetector

st.set_page_config(page_title="Polyglot Ghost Voice Auth", layout="wide")

st.title("The Polyglot Ghost Voice Authenticator")
st.markdown("Authenticate whether the speaking voice matches the signature voice AND detect if it's an AI clone.")

# Initialize detectors in session state
if 'detector' not in st.session_state:
    st.session_state.detector = RealtimeVoiceDetector()
if 'robust_detector' not in st.session_state:
    st.session_state.robust_detector = RobustVoiceDetector()
if 'baseline_set' not in st.session_state:
    st.session_state.baseline_set = False

# Sidebar for controls
with st.sidebar:
    st.header("Settings")
    strictness = st.selectbox(
        "Matching Strictness", 
        ["strict", "normal", "relaxed", "very_relaxed"], 
        index=1,
        help="Strict: High security, low tolerance. Very Relaxed: High tolerance for sickness/microphone differences"
    )

# Two-column layout
col1, col2 = st.columns(2)

with col1:
    st.header("1. Set Signature (Baseline)")
    st.markdown("Record or upload your voice to establish an identity signature.")
    
    baseline_audio = st.audio_input("Record Baseline Voice")
    baseline_upload = st.file_uploader("Or Upload Baseline (.wav)", type=['wav'], key="base_upload")
    
    baseline_to_use = baseline_audio if baseline_audio else baseline_upload
    
    if baseline_to_use is not None:
        st.audio(baseline_to_use)
        if st.button("Set as Signature"):
            # Save Temp
            with open("temp_baseline.wav", "wb") as f:
                f.write(baseline_to_use.getbuffer())
                
            with st.spinner("Extracting signature features..."):
                success = st.session_state.detector.set_baseline("temp_baseline.wav")
                if success:
                    st.session_state.robust_detector.set_baseline(st.session_state.detector.baseline_features)
                    st.session_state.baseline_set = True
                    st.success("✅ Signature successfully established!")
                else:
                    st.error("Failed to extract features. Audio might be corrupted or too silent.")

with col2:
    st.header("2. Test Voice")
    st.markdown("Record or upload the test voice to verify against the signature.")
    
    test_audio = st.audio_input("Record Test Voice")
    test_upload = st.file_uploader("Or Upload Test (.wav)", type=['wav'], key="test_upload")
    
    test_to_use = test_audio if test_audio else test_upload
    
    if test_to_use is not None:
        st.audio(test_to_use)
        
        if st.button("Analyze Audio"):
            if not st.session_state.baseline_set:
                st.warning("⚠️ Please set a Signature Voice in Step 1 first!")
            else:
                with st.spinner("Analyzing..."):
                    with open("temp_test.wav", "wb") as f:
                        f.write(test_to_use.getbuffer())
                        
                    # Load and analyze
                    import soundfile as sf
                    y, sr = sf.read("temp_test.wav")
                    if len(y.shape) > 1:
                        y = y.mean(axis=1) # Mono
                        
                    result = st.session_state.detector.analyze_chunk(y, sr)
                    
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        features = result["features"]
                        robust_res = st.session_state.robust_detector.analyze(features, strictness=strictness)
                        
                        st.divider()
                        
                        # --- Display Results ---
                        
                        # AI VS HUMAN Check
                        if robust_res["is_ai_generated"]:
                            st.error(f"🚨 **AI GENERATED VOICE DETECTED** (Phase Artifacts Too High)")
                        else:
                            st.success(f"🗣️ **Voice Appears Human**")
                        
                        # Identity Matching Check
                        if robust_res["is_match"]:
                            st.success(f"✅ **IDENTITY MATCH:** This matches the Signature Voice!")
                        else:
                            st.warning(f"❌ **IDENTITY MISMATCH:** This is a different person!")
                            
                        # Metrics display
                        st.markdown("### Analysis Metrics")
                        m_col1, m_col2, m_col3 = st.columns(3)
                        m_col1.metric("Confidence Score", f"{robust_res['confidence']:.1%}")
                        m_col2.metric("Identity Deviation", f"{robust_res['deviation']:.1%}")
                        m_col3.metric("Risk Level", robust_res['risk_level'])
                        
                        # Detailed Breakdown
                        with st.expander("Detailed Feature Breakdown"):
                            st.json({
                                "Verdict": robust_res['verdict'],
                                "MFCC Similarity (Identity)": f"{robust_res['mfcc_similarity']:.1%}",
                                "Spectral Similarity (Tone)": f"{robust_res['spectral_similarity']:.1%}",
                                "Phase Similarity (Authenticity)": f"{robust_res['phase_similarity']:.1%}"
                            })

# Cleanup
if os.path.exists("temp_baseline.wav"):
    try: os.remove("temp_baseline.wav")
    except: pass
if os.path.exists("temp_test.wav"):
    try: os.remove("temp_test.wav")
    except: pass
