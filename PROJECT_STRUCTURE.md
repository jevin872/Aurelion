# The Polyglot Ghost - Project Structure

## Essential Files Only

### Root Files
- `train.py` - Train the voice authentication model
- `requirements.txt` - Python dependencies
- `classifier_params.json` - Trained model parameters (generated)
- `features.json` - Extracted features (generated)
- `README.md` - Project documentation
- `.env` - Environment variables
- `.gitignore` - Git ignore rules

### Backend (Core Logic)
- `backend/feature_extraction_fast.py` - Fast parallel feature extraction (MFCC, Phase, Spectral)
- `backend/train_model.py` - Model training logic
- `backend/realtime_detector.py` - Real-time voice detection engine
- `backend/robust_detector.py` - Illness-tolerant voice matching
- `backend/audio_normalizer.py` - Audio length normalization (3.5s)
- `backend/utils.py` - Utility functions (jitter calculation)

### Frontend (User Interface)
- `frontend/dashboard.py` - Main Streamlit dashboard

### Data Folders
- `small_data/` - Training audio samples (250 files)
- `dataset/fake/` - Fake voice samples for testing
- `dataset/real/` - Real voice samples for testing
- `dataset/test/` - Test audio files
- `data/` - Empty folder for additional data

### Virtual Environment
- `ven/` - Python virtual environment (not tracked in git)

## Workflow

### 1. Train Model
```bash
python train.py
```
- Extracts features from `small_data/` (250 audio files)
- Trains classifier using phase discontinuity threshold
- Generates `features.json` and `classifier_params.json`
- Takes ~30 seconds with parallel processing

### 2. Run Dashboard
```bash
streamlit run frontend/dashboard.py
```
- Opens at http://localhost:8501
- Record voice signature (upload or live recording)
- Test recordings against signature
- Get instant match/mismatch results

## Key Features

### Feature Extraction
- **MFCC** (85% weight) - Speaker identity
- **Phase Discontinuity** (5% weight) - AI detection
- **Spectral Centroid** (10% weight) - Voice characteristics
- **Jitter** (0% weight) - Ignored (too variable)

### Voice Matching
- MFCC similarity > 80% = automatic match
- Adaptive thresholds: Strict (30%), Normal (50%), Relaxed (70%), Very Relaxed (85%)
- Default: Very Relaxed for same-voice tolerance

### AI Detection
- Phase discontinuity > 2.09 threshold
- Only flags as AI if MFCC similarity < 70% (different speaker)

## Removed Files (Unnecessary)
- - `DockerFile` - Not configured
- - `frontend/forensic_dashboard.py` - Duplicate
- - `backend/api_enhanced.py` - Not used
- - `backend/main.py` - Not used
- - `backend/data.py` - Not used
- - `backend/test_conn.py` - Not used
- - `test/ver.py` - Not needed
- - `SAME_VOICE_FIX.md` - Temporary docs
- - `START.md` - Redundant
- - `requirements_clean.txt` - Duplicate
- - `.roo/` - Not needed

## Clean Project
Total essential files: ~15 Python files + data folders
