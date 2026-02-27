import os
import streamlit as st
import requests
from io import BytesIO

# Configuration - Get from environment or Streamlit secrets
try:
    API_URL = st.secrets.get("API_URL", os.getenv("API_URL", "http://localhost:8000"))
except:
    API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Polyglot Ghost Voice Auth", layout="wide")

st.title("The Polyglot Ghost Voice Authenticator")
st.markdown("Authenticate whether the speaking voice matches the signature voice AND detect if it's an AI clone.")

# Initialize session state
if 'baseline_set' not in st.session_state:
    st.session_state.baseline_set = False

# Sidebar for controls
with st.sidebar:
    st.header("Settings")
    api_status = "🟢 Connected" if API_URL and API_URL != "http://localhost:8000" else "🔴 Not configured"
    st.markdown(f"**API Status:** {api_status}")
    
    strictness = st.selectbox(
        "Matching Strictness", 
        ["strict", "normal", "relaxed", "very_relaxed"], 
        index=1,
        help="Strict: High security, low tolerance. Very Relaxed: High tolerance for sickness/microphone differences"
    )
    
    if st.button("Reset Baseline"):
        try:
            response = requests.post(f"{API_URL}/api/reset")
            if response.status_code == 200:
                st.session_state.baseline_set = False
                st.success("Baseline reset successfully!")
            else:
                st.error("Failed to reset baseline")
        except Exception as e:
            st.error(f"Error: {str(e)}")

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
            with st.spinner("Extracting signature features... (may take 30-60s on first request)"):
                try:
                    # Prepare file for upload
                    files = {"file": ("baseline.wav", baseline_to_use, "audio/wav")}
                    
                    # Send to API
                    response = requests.post(f"{API_URL}/api/set-baseline", files=files, timeout=120)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.baseline_set = True
                        st.success("Signature successfully established!")
                    else:
                        error_detail = response.json().get("detail", "Unknown error")
                        st.error(f"Failed: {error_detail}")
                
                except requests.Timeout:
                    st.warning("Request timed out. The backend may be starting up (cold start). Please try again in 30 seconds.")
                except Exception as e:
                    st.error(f"Error connecting to API: {str(e)}")

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
                st.warning("Please set a Signature Voice in Step 1 first!")
            else:
                with st.spinner("Analyzing..."):
                    try:
                        # Prepare file for upload
                        files = {"file": ("test.wav", test_to_use, "audio/wav")}
                        
                        # Send to API
                        response = requests.post(
                            f"{API_URL}/api/analyze",
                            files=files,
                            params={"strictness": strictness},
                            timeout=120
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            
                            st.divider()
                            
                            # Display Results
                            if result["is_ai_generated"]:
                                st.error("AI GENERATED VOICE DETECTED (Phase Artifacts Too High)")
                            else:
                                st.success("Voice Appears Human")
                            
                            if result["is_match"]:
                                st.success("IDENTITY MATCH: This matches the Signature Voice!")
                            else:
                                st.warning("IDENTITY MISMATCH: This is a different person!")
                            
                            # Metrics display
                            st.markdown("### Analysis Metrics")
                            m_col1, m_col2, m_col3 = st.columns(3)
                            m_col1.metric("Confidence Score", f"{result['confidence']:.1%}")
                            m_col2.metric("Identity Deviation", f"{result['deviation']:.1%}")
                            m_col3.metric("Risk Level", result['risk_level'])
                            
                            # Detailed Breakdown
                            with st.expander("Detailed Feature Breakdown"):
                                st.json({
                                    "Verdict": result['verdict'],
                                    "MFCC Similarity (Identity)": f"{result['mfcc_similarity']:.1%}",
                                    "Spectral Similarity (Tone)": f"{result['spectral_similarity']:.1%}",
                                    "Phase Similarity (Authenticity)": f"{result['phase_similarity']:.1%}"
                                })
                        else:
                            error_detail = response.json().get("detail", "Unknown error")
                            st.error(f"Analysis failed: {error_detail}")
                    
                    except requests.Timeout:
                        st.warning("Request timed out. Please try again.")
                    except Exception as e:
                        st.error(f"Error connecting to API: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Backend API on Render | Frontend on Streamlit Cloud")
