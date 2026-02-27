"""
The Polyglot Ghost - Voice Authentication Dashboard
1. Capture user's voice signature (upload or live recording)
2. Compare subsequent recordings against signature
"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import librosa
import soundfile as sf
import json
from pathlib import Path
import sys
import time
import io

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.realtime_detector import RealtimeVoiceDetector
from backend.robust_detector import RobustVoiceDetector

# Try to import audio recorder
try:
    from audio_recorder_streamlit import audio_recorder
    AUDIO_RECORDER_AVAILABLE = True
except ImportError:
    AUDIO_RECORDER_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="The Polyglot Ghost",
    page_icon="🎙️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .signature-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 1rem;
        text-align: center;
        margin: 1rem 0;
    }
    .alert-fake {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .alert-real {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'detector' not in st.session_state:
    st.session_state.detector = RealtimeVoiceDetector()
if 'robust_detector' not in st.session_state:
    st.session_state.robust_detector = RobustVoiceDetector()
if 'use_robust' not in st.session_state:
    st.session_state.use_robust = True  # Default to robust mode
if 'tolerance_level' not in st.session_state:
    st.session_state.tolerance_level = 'normal'  # Changed default to 'normal'
if 'signature_set' not in st.session_state:
    st.session_state.signature_set = False
if 'signature_file' not in st.session_state:
    st.session_state.signature_file = None
if 'analysis_count' not in st.session_state:
    st.session_state.analysis_count = 0


def plot_waveform(audio_data, sr, title="Audio Waveform"):
    """Plot audio waveform."""
    time_axis = np.arange(len(audio_data)) / sr
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=time_axis,
        y=audio_data,
        mode='lines',
        line=dict(color='#1f77b4', width=1),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.3)'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Time (seconds)",
        yaxis_title="Amplitude",
        height=300,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig


def plot_comparison(signature_data, test_data, sr):
    """Plot signature vs test audio comparison."""
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Your Voice Signature', 'Test Recording'),
        vertical_spacing=0.15
    )
    
    # Signature
    time_sig = np.arange(len(signature_data)) / sr
    fig.add_trace(
        go.Scatter(x=time_sig, y=signature_data, mode='lines',
                   line=dict(color='#2ca02c'), name='Signature'),
        row=1, col=1
    )
    
    # Test
    time_test = np.arange(len(test_data)) / sr
    fig.add_trace(
        go.Scatter(x=time_test, y=test_data, mode='lines',
                   line=dict(color='#1f77b4'), name='Test'),
        row=2, col=1
    )
    
    fig.update_xaxes(title_text="Time (s)")
    fig.update_yaxes(title_text="Amplitude")
    fig.update_layout(height=500, showlegend=False)
    
    return fig


def plot_feature_comparison(signature_features, test_features):
    """Plot feature comparison radar chart."""
    categories = ['Phase\nDiscontinuity', 'Spectral\nCentroid', 'Jitter']
    
    # Normalize features
    sig_values = [
        min(signature_features.get('phase_discontinuity_mean', 0) / 3.0, 1.0),
        min(signature_features.get('spectral_centroid_mean', 0) / 5000.0, 1.0),
        min(signature_features.get('jitter', 0) / 0.01, 1.0),
    ]
    
    test_values = [
        min(test_features.get('phase_discontinuity_mean', 0) / 3.0, 1.0),
        min(test_features.get('spectral_centroid_mean', 0) / 5000.0, 1.0),
        min(test_features.get('jitter', 0) / 0.01, 1.0),
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=sig_values,
        theta=categories,
        fill='toself',
        name='Your Signature',
        line_color='#2ca02c'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=test_values,
        theta=categories,
        fill='toself',
        name='Test Recording',
        line_color='#1f77b4'
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        height=400,
        title='Feature Profile Comparison'
    )
    
    return fig


def analyze_voice_robust(test_audio, test_sr):
    """
    Analyze voice using robust detector with illness tolerance.
    
    Args:
        test_audio: Audio samples
        test_sr: Sample rate
    
    Returns:
        Enhanced result dictionary
    """
    # Get features from standard detector
    result = st.session_state.detector.analyze_chunk(test_audio, test_sr)
    
    # If baseline is set, use robust analysis
    if st.session_state.robust_detector.baseline_features:
        test_features = result.get('features', {})
        robust_result = st.session_state.robust_detector.analyze(test_features)
        
        # Merge results
        result.update({
            'is_match_robust': robust_result['is_match'],
            'confidence_robust': robust_result['confidence'],
            'deviation_robust': robust_result['deviation'],
            'threshold_robust': robust_result['threshold'],
            'threshold_level': robust_result['threshold_level'],
            'verdict_robust': robust_result['verdict'],
            'is_ai_generated': robust_result['is_ai_generated'],
            'feature_breakdown': robust_result['feature_breakdown']
        })
        
        # Override with robust results
        result['is_fake'] = not robust_result['is_match'] or robust_result['is_ai_generated']
        result['confidence'] = robust_result['confidence']
        result['baseline_deviation'] = robust_result['deviation']
        result['verdict'] = robust_result['verdict']
        result['risk_level'] = robust_result['risk_level']
    
    return result


# Header
st.markdown('<div class="main-header">The Polyglot Ghost</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Voice Authentication System</div>', unsafe_allow_html=True)

# Main workflow
if not st.session_state.signature_set:
    # STEP 1: Capture signature
    st.markdown("## Step 1: Record Your Voice Signature")
    st.info("Upload a recording of your voice OR record live. This will be your authentication signature.")
    
    # Tabs for upload vs live recording
    tab1, tab2 = st.tabs(["Upload File", "Live Recording"])
    
    with tab1:
        signature_file = st.file_uploader(
            "Upload your voice recording (WAV format)",
            type=['wav'],
            key='signature_upload'
        )
        
        if signature_file:
            # Preview signature
            st.audio(signature_file, format='audio/wav')
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if st.button("Set as My Signature", type="primary", key='set_upload'):
                    with st.spinner("Processing your voice signature..."):
                        # Save temporarily
                        temp_path = Path("temp_signature.wav")
                        with open(temp_path, 'wb') as f:
                            f.write(signature_file.read())
                        
                        # Set baseline
                        if st.session_state.detector.set_baseline(str(temp_path)):
                            st.session_state.signature_set = True
                            st.session_state.signature_file = signature_file.name
                            
                            # Load for display
                            audio_data, sr = librosa.load(str(temp_path), sr=16000)
                            st.session_state.signature_audio = audio_data
                            st.session_state.signature_sr = sr
                            
                            # Also set robust detector baseline
                            baseline_features = st.session_state.detector.baseline_features
                            st.session_state.robust_detector.set_baseline(baseline_features)
                            
                            temp_path.unlink()
                            st.rerun()
                        else:
                            st.error("Failed to process signature")
                            temp_path.unlink()
            
            with col2:
                # Show waveform preview
                temp_path = Path("temp_preview.wav")
                with open(temp_path, 'wb') as f:
                    signature_file.seek(0)
                    f.write(signature_file.read())
                
                audio_data, sr = librosa.load(str(temp_path), sr=16000)
                fig = plot_waveform(audio_data, sr, "Your Voice Preview")
                st.plotly_chart(fig)
                
                temp_path.unlink()
    
    with tab2:
        st.markdown("### Record Your Voice")
        
        if AUDIO_RECORDER_AVAILABLE:
            st.info("Click the microphone button below to start recording. Speak clearly for 3-5 seconds, then click stop.")
            
            audio_bytes = audio_recorder(
                text="Click to record",
                recording_color="#e74c3c",
                neutral_color="#3498db",
                icon_name="microphone",
                icon_size="3x",
                key="signature_recorder"
            )
            
            if audio_bytes:
                st.success("Recording captured!")
                
                # Save to proper WAV format first
                temp_playback = Path("temp_sig_playback.wav")
                with open(temp_playback, 'wb') as f:
                    f.write(audio_bytes)
                
                # Play back the recording
                st.markdown("**Playback your recording:**")
                with open(temp_playback, 'rb') as f:
                    st.audio(f.read(), format='audio/wav', start_time=0)
                
                # Show waveform preview
                audio_data, sr = librosa.load(str(temp_playback), sr=16000)
                
                # Display duration
                duration = len(audio_data) / sr
                st.info(f"Recording duration: {duration:.2f} seconds - Normalized to 3.5s for analysis")
                
                if duration < 3.0:
                    st.warning("Recording is short. For best results, record for 3-5 seconds.")
                elif duration > 10.0:
                    st.info("Long recording detected. Using best 3.5s segment with highest speech energy.")
                
                fig = plot_waveform(audio_data, sr, "Your Voice Preview")
                st.plotly_chart(fig)
                
                temp_playback.unlink()
                
                # Set signature button
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("Set as My Signature", type="primary", key='set_live'):
                        with st.spinner("Processing your voice signature..."):
                            # Save temporarily
                            temp_path = Path("temp_signature_live.wav")
                            with open(temp_path, 'wb') as f:
                                f.write(audio_bytes)
                            
                            # Set baseline
                            if st.session_state.detector.set_baseline(str(temp_path)):
                                st.session_state.signature_set = True
                                st.session_state.signature_file = "Live Recording"
                                
                                # Load for display
                                audio_data, sr = librosa.load(str(temp_path), sr=16000)
                                st.session_state.signature_audio = audio_data
                                st.session_state.signature_sr = sr
                                
                                # Also set robust detector baseline
                                baseline_features = st.session_state.detector.baseline_features
                                st.session_state.robust_detector.set_baseline(baseline_features)
                                
                                temp_path.unlink()
                                st.success("Signature set successfully!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to process signature")
                                temp_path.unlink()
                
                with col2:
                    if st.button("Record Again"):
                        st.rerun()
        else:
            st.warning("Live recording not available. Please install: `pip install audio-recorder-streamlit`")
            st.code("pip install audio-recorder-streamlit", language="bash")
            st.info("For now, please use the 'Upload File' tab to set your signature.")

else:
    # STEP 2: Test recordings
    st.markdown('<div class="signature-box">', unsafe_allow_html=True)
    st.markdown(f"### Voice Signature Active")
    st.markdown(f"**File:** {st.session_state.signature_file}")
    st.markdown(f"**Analyses Performed:** {st.session_state.analysis_count}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("Reset Signature"):
            st.session_state.signature_set = False
            st.session_state.signature_file = None
            st.session_state.analysis_count = 0
            st.session_state.detector.reset()
            st.rerun()
    
    st.markdown("---")
    st.markdown("## Test Voice Recording")
    st.info("Upload a voice recording OR record live to verify if it matches your signature.")
    
    # Tabs for upload vs live recording
    test_tab1, test_tab2 = st.tabs(["Upload File", "Live Recording"])
    
    with test_tab1:
        test_file = st.file_uploader(
            "Upload voice recording to test",
            type=['wav'],
            key='test_upload'
        )
        
        if test_file:
            st.audio(test_file, format='audio/wav')
            
            if st.button("Analyze Recording", type="primary", key='analyze_upload'):
                with st.spinner("Analyzing voice..."):
                    # Save temporarily
                    temp_path = Path("temp_test.wav")
                    with open(temp_path, 'wb') as f:
                        f.write(test_file.read())
                    
                    # Load audio
                    test_audio, test_sr = librosa.load(str(temp_path), sr=16000)
                    
                    # Analyze
                    result = analyze_voice_robust(test_audio, test_sr)
                    st.session_state.analysis_count += 1
                    
                    # Store for display
                    st.session_state.last_result = result
                    st.session_state.last_test_audio = test_audio
                    
                    temp_path.unlink()
    
    with test_tab2:
        st.markdown("### Record Voice to Test")
        
        if AUDIO_RECORDER_AVAILABLE:
            st.info("Click the microphone button to record. Speak clearly for 3-5 seconds, then click stop.")
            
            test_audio_bytes = audio_recorder(
                text="Click to record",
                recording_color="#e74c3c",
                neutral_color="#3498db",
                icon_name="microphone",
                icon_size="3x",
                key="test_recorder"
            )
            
            if test_audio_bytes:
                st.success("Recording captured!")
                
                # Save to proper WAV format first
                temp_playback = Path("temp_playback.wav")
                with open(temp_playback, 'wb') as f:
                    f.write(test_audio_bytes)
                
                # Play back the recording
                st.markdown("**Playback your recording:**")
                with open(temp_playback, 'rb') as f:
                    st.audio(f.read(), format='audio/wav', start_time=0)
                
                # Show waveform preview
                audio_data, sr = librosa.load(str(temp_playback), sr=16000)
                
                # Display duration
                duration = len(audio_data) / sr
                st.info(f"Recording duration: {duration:.2f} seconds - Normalized to 3.5s for analysis")
                
                if duration < 3.0:
                    st.warning("Recording is short. For best results, record for 3-5 seconds.")
                elif duration > 10.0:
                    st.info("Long recording detected. Using best 3.5s segment with highest speech energy.")
                
                fig = plot_waveform(audio_data, sr, "Test Recording Preview")
                st.plotly_chart(fig)
                
                temp_playback.unlink()
                
                # Analyze button
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("Analyze Recording", type="primary", key='analyze_live'):
                        with st.spinner("Analyzing voice..."):
                            # Save temporarily
                            temp_path = Path("temp_test_live.wav")
                            with open(temp_path, 'wb') as f:
                                f.write(test_audio_bytes)
                            
                            # Load audio
                            test_audio, test_sr = librosa.load(str(temp_path), sr=16000)
                            
                            # Analyze
                            result = analyze_voice_robust(test_audio, test_sr)
                            st.session_state.analysis_count += 1
                            
                            # Store for display
                            st.session_state.last_result = result
                            st.session_state.last_test_audio = test_audio
                            
                            temp_path.unlink()
                            st.rerun()
                
                with col2:
                    if st.button("Record Again"):
                        st.rerun()
        else:
            st.warning("Live recording not available. Please install: `pip install audio-recorder-streamlit`")
            st.code("pip install audio-recorder-streamlit", language="bash")
    
    # Display results if available
    if 'last_result' in st.session_state and st.session_state.last_result:
        result = st.session_state.last_result
        test_audio = st.session_state.last_test_audio
        
        st.markdown("---")
        st.markdown("## Analysis Results")
        
        verdict = result.get('verdict', 'Unknown')
        is_fake = result.get('is_fake', False)
        confidence = result.get('confidence', 0)
        baseline_deviation = result.get('baseline_deviation', 0)
        
        # Determine if it's a mismatch based on deviation threshold
        # If deviation > 30%, it's a mismatch regardless of is_fake
        is_mismatch = is_fake or (baseline_deviation and baseline_deviation > 0.30)
        
        # Verdict box
        if is_mismatch:
            st.markdown(f'<div class="alert-fake">', unsafe_allow_html=True)
            st.markdown(f"### VOICE MISMATCH DETECTED")
            st.markdown(f"This recording does NOT match your voice signature!")
            st.markdown(f"**Confidence:** {confidence:.1%}")
            if baseline_deviation:
                st.markdown(f"**Deviation from Signature:** {baseline_deviation:.1%}")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alert-real">', unsafe_allow_html=True)
            st.markdown(f"### VOICE MATCH CONFIRMED")
            st.markdown(f"This recording matches your voice signature!")
            st.markdown(f"**Confidence:** {confidence:.1%}")
            if baseline_deviation:
                st.markdown(f"**Deviation from Signature:** {baseline_deviation:.1%}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Match Status", "NO" if is_mismatch else "YES")
        with col2:
            st.metric("Confidence", f"{confidence:.1%}")
        with col3:
            # Show MFCC similarity if available, or phase/spectral similarity
            mfcc_sim = result.get('mfcc_similarity', None)
            phase_sim = result.get('phase_similarity', None)
            spectral_sim = result.get('spectral_similarity', None)
            
            if mfcc_sim is not None and mfcc_sim > 0:
                st.metric("MFCC Similarity", f"{mfcc_sim:.1%}")
            elif phase_sim is not None and spectral_sim is not None:
                avg_sim = (phase_sim + spectral_sim) / 2
                st.metric("Feature Similarity", f"{avg_sim:.1%}")
            elif baseline_deviation:
                st.metric("Deviation", f"{baseline_deviation:.1%}")
            else:
                st.metric("Deviation", "N/A")
        with col4:
            st.metric("Risk Level", result.get('risk_level', 'UNKNOWN'))
        
        # Visualizations
        st.markdown("### Waveform Comparison")
        fig_comp = plot_comparison(
            st.session_state.signature_audio,
            test_audio,
            16000
        )
        st.plotly_chart(fig_comp)
        
        # Feature comparison
        st.markdown("### Feature Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Radar chart
            sig_features = st.session_state.detector.baseline_features
            test_features = result.get('features', {})
            
            fig_radar = plot_feature_comparison(sig_features, test_features)
            st.plotly_chart(fig_radar)
        
        with col2:
            # Feature table
            st.markdown("**Key Features:**")
            
            features_data = {
                "Feature": [
                    "Phase Discontinuity",
                    "Spectral Centroid",
                    "Jitter"
                ],
                "Your Signature": [
                    f"{sig_features.get('phase_discontinuity_mean', 0):.4f}",
                    f"{sig_features.get('spectral_centroid_mean', 0):.2f}",
                    f"{sig_features.get('jitter', 0):.6f}"
                ],
                "Test Recording": [
                    f"{test_features.get('phase_discontinuity_mean', 0):.4f}",
                    f"{test_features.get('spectral_centroid_mean', 0):.2f}",
                    f"{test_features.get('jitter', 0):.6f}"
                ]
            }
            
            st.table(features_data)

# Sidebar
with st.sidebar:
    st.header("Settings")
    
    # Tolerance level selector
    st.subheader("Voice Matching Tolerance")
    st.info("Higher tolerance = works better when sick/tired")
    
    tolerance = st.select_slider(
        "Tolerance Level",
        options=['strict', 'normal', 'relaxed', 'very_relaxed'],
        value=st.session_state.tolerance_level,
        format_func=lambda x: {
            'strict': 'Strict (25%)',
            'normal': 'Normal (45%)',
            'relaxed': 'Relaxed (65%)',
            'very_relaxed': 'Very Relaxed (80%)'
        }[x]
    )
    
    if tolerance != st.session_state.tolerance_level:
        st.session_state.tolerance_level = tolerance
        st.session_state.robust_detector.set_tolerance(tolerance)
        st.success(f"Tolerance set to: {tolerance}")
    
    st.markdown("""
    **Tolerance Levels:**
    - **Strict**: Exact match required (25%)
    - **Normal**: Standard matching (45%) - Recommended
    - **Relaxed**: Works when sick/tired (65%)
    - **Very Relaxed**: Maximum tolerance (80%) 
    
    **Note:** Same voice should match at Normal level!
    """)
    
    st.divider()
    
    st.header("About")
    st.markdown("""
    **The Polyglot Ghost** detects AI-generated voices and verifies voice authenticity.
    
    **How it works:**
    1. Record your voice signature
    2. Test recordings are compared to your signature
    3. Get instant match/mismatch results
    
    **Features analyzed:**
    - **MFCC (45%)**: Speaker identity
    - **Phase (30%)**: AI detection
    - **Spectral (25%)**: Voice characteristics
    - **Jitter (0%)**: Ignored - too variable
    
    **Matching criteria:**
    - High MFCC similarity (>90%) AND
    - Similar spectral features (<30% difference)
    - OR weighted deviation < threshold
    """)
    
    st.divider()
    
    if st.session_state.signature_set:
        st.header("Statistics")
        stats = st.session_state.detector.get_statistics()
        if stats:
            st.metric("Total Analyses", st.session_state.analysis_count)
            st.metric("Chunks Analyzed", stats.get('total_chunks_analyzed', 0))

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p><strong>The Polyglot Ghost</strong> - Voice Authentication System</p>
    <p>Powered by MFCC, STFT, and Phase Continuity Analysis</p>
</div>
""", unsafe_allow_html=True)
