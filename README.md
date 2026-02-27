# The Polyglot Ghost 👻

## Voice Authentication System

A streamlined voice authentication system that captures your voice signature and verifies subsequent recordings against it. Detects AI-generated voices and voice mismatches using MFCC, STFT, and Phase Continuity analysis.

---

## 🚀 Quick Start (2 Steps)

### 1. Train the Model
```bash
python train.py
```
This automatically trains on the audio files in `small_data/` (takes ~30 seconds with parallel processing).

### 2. Launch Dashboard
```bash
streamlit run frontend/dashboard.py
```
Open http://localhost:8501 in your browser.

---

## 📋 How It Works

### Step 1: Record Your Voice Signature
- Upload a recording of your voice
- System extracts your unique voice features
- This becomes your authentication baseline

### Step 2: Test Recordings
- Upload any voice recording to test
- System compares it against your signature
- Get instant match/mismatch results with confidence scores

---

## 🎯 Use Cases

- **Banking**: Verify caller identity during phone banking
- **Security**: Authenticate users by voice
- **Personal**: Detect if someone is impersonating you
- **AI Detection**: Identify AI-generated voices

---

## 📁 Project Structure

```
.
├── backend/
│   ├── feature_extraction_fast.py  # Fast parallel feature extraction
│   ├── realtime_detector.py        # Real-time detection engine
│   ├── train_model.py              # Model training
│   ├── api_enhanced.py             # API server (optional)
│   ├── utils.py                    # Utilities
│   └── data.py                     # Dataset download
├── frontend/
│   └── dashboard.py                # Main dashboard
├── small_data/                     # Training audio (250 files)
├── train.py                        # Simple training script
└── requirements_clean.txt          # Dependencies
```

---

## 🔧 Installation

### Prerequisites
- Python 3.8+
- pip

### Install Dependencies
```bash
pip install -r requirements_clean.txt
```

### Optional: Download Training Data
If you don't have `small_data/` folder:
```bash
python backend/data.py
```

---

## 📊 Features Analyzed

### Phase Continuity (Primary Indicator)
- Detects unnatural phase patterns in AI voices
- Most discriminative feature for deepfake detection

### MFCC (Mel-Frequency Cepstral Coefficients)
- Captures spectral characteristics
- 40 coefficients + statistics = 120 features

### STFT (Short-Time Fourier Transform)
- Spectral centroid, rolloff, bandwidth
- 8 spectral features

### Jitter Analysis
- Vocal periodicity measurement
- Natural vs synthetic voice patterns

**Total: 135+ features per audio sample**

---

## 🎨 Dashboard Features

### Voice Signature Setup
- Upload your voice recording
- Visual waveform preview
- One-click signature activation

### Voice Testing
- Upload test recordings
- Real-time analysis (<100ms)
- Match/mismatch detection

### Visualizations
- Waveform comparison (signature vs test)
- Feature radar charts
- Detailed metrics table
- Confidence scoring

### Results
- ✅ **Match Confirmed**: Recording matches your signature
- ⚠️ **Mismatch Detected**: Recording does NOT match
- Confidence percentage
- Deviation from baseline
- Risk level assessment

---

## 🔬 Technical Details

### Performance
- **Latency**: <100ms per analysis
- **Training Time**: ~30 seconds (250 files)
- **Accuracy**: 70-85% baseline
- **Parallel Processing**: Uses all CPU cores

### Detection Method
1. Extract 135+ features from audio
2. Compare against baseline signature
3. Calculate deviation and confidence
4. Determine match/mismatch

### Key Metrics
- **Phase Discontinuity**: Primary AI detection indicator
- **Baseline Deviation**: How different from your voice
- **Confidence Score**: Reliability of the verdict
- **Risk Level**: MINIMAL/LOW/MEDIUM/HIGH

---

## 🌐 API Usage (Optional)

Start the API server:
```bash
python backend/api_enhanced.py
```

### Analyze Audio
```bash
curl -X POST "http://localhost:8000/analyze-voice" \
  -F "file=@audio.wav"
```

### Set Baseline
```bash
curl -X POST "http://localhost:8000/set-baseline" \
  -F "file=@your_voice.wav"
```

### WebSocket Streaming
```python
import websockets
import asyncio

async def stream_audio():
    async with websockets.connect('ws://localhost:8000/ws/stream') as ws:
        await ws.send(audio_chunk.tobytes())
        result = await ws.recv()
```

---

## 🛠️ Troubleshooting

### "No module named 'librosa'"
```bash
pip install -r requirements_clean.txt
```

### "small_data directory not found"
```bash
python backend/data.py
```

### Training is slow
The system uses parallel processing automatically. Training 250 files should take ~30 seconds on a modern CPU.

### Dashboard won't start
```bash
pip install streamlit
streamlit run frontend/dashboard.py
```

---

## 📈 Improving Accuracy

1. **More Training Data**: Add more audio samples to `small_data/`
2. **Better Signature**: Use a longer, clearer voice recording
3. **Multiple Tests**: Test several recordings for consistency
4. **Retrain**: Run `python train.py` after adding new data

---

## 🔒 Privacy & Security

- Audio files are processed locally
- No data sent to external servers (except Featherless for training)
- Signatures stored in memory only
- No permanent storage of voice data

---

## 📚 How Phase Continuity Works

AI voice generators (TTS, voice cloning) produce audio through:
1. **Vocoders**: Convert features back to audio
2. **Neural Networks**: Approximate waveforms

These processes create **phase discontinuities** - unnatural jumps in the phase information that human vocal cords don't produce.

The Polyglot Ghost detects these artifacts by:
- Analyzing phase derivatives
- Measuring phase consistency
- Comparing unwrapped phase patterns

---

## 🎓 Understanding the Results

### Match Confirmed ✅
- Recording matches your voice signature
- Low deviation from baseline
- High confidence score
- Likely authentic

### Mismatch Detected ⚠️
- Recording does NOT match your signature
- High deviation from baseline
- Could be:
  - Different person
  - AI-generated voice
  - Manipulated audio
  - Poor quality recording

### Confidence Score
- **>80%**: High confidence in verdict
- **50-80%**: Medium confidence
- **<50%**: Low confidence, manual review recommended

### Deviation Percentage
- **<10%**: Very similar to signature
- **10-30%**: Moderate difference
- **>30%**: Significant difference

---

## 🚀 Next Steps

1. ✅ Train the model: `python train.py`
2. ✅ Launch dashboard: `streamlit run frontend/dashboard.py`
3. ✅ Record your voice signature
4. ✅ Test with different recordings
5. ✅ Experiment with AI-generated voices

---

## 🤝 Use Cases in Action

### Banking Authentication
```
1. Customer calls bank
2. System: "Please say: I authorize this transaction"
3. Customer speaks
4. System compares to stored signature
5. ✅ Match → Transaction approved
   ⚠️ Mismatch → Additional verification required
```

### Security Access
```
1. User attempts voice login
2. System: "Please speak your passphrase"
3. User speaks
4. System verifies against signature
5. ✅ Match → Access granted
   ⚠️ Mismatch → Access denied
```

### AI Detection
```
1. Upload suspicious audio
2. System analyzes phase patterns
3. Compares to known human voice characteristics
4. ✅ Human voice detected
   ⚠️ AI-generated voice detected
```

---

## 📞 Support

For issues or questions:
- Check this README
- Review the dashboard tooltips
- Test with different audio files
- Retrain if needed

---

## 🎯 Key Features

- ✅ **Fast Training**: ~30 seconds for 250 files
- ✅ **Real-time Analysis**: <100ms per recording
- ✅ **User-Friendly**: Simple 2-step workflow
- ✅ **Visual Feedback**: Waveforms and charts
- ✅ **High Accuracy**: 70-85% detection rate
- ✅ **Privacy-Focused**: Local processing
- ✅ **Scalable**: API available for integration

---

**The Polyglot Ghost** - Securing voice communications in the age of AI 🛡️👻

*"In a world where voices can be cloned, trust must be verified."*
