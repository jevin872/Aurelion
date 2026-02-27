# System Architecture

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         USER                                │
│                    (Web Browser)                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              STREAMLIT CLOUD (Frontend)                     │
│              https://your-app.streamlit.app                 │
├─────────────────────────────────────────────────────────────┤
│  • streamlit_app.py                                         │
│  • Audio recording/upload interface                         │
│  • Results visualization                                    │
│  • Metrics display                                          │
│  • Session state management                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP REST API
                         │ (POST /api/set-baseline)
                         │ (POST /api/analyze)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              RENDER (Backend API)                           │
│              https://your-api.onrender.com                  │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Application (backend/api.py)                       │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Endpoints:                                           │ │
│  │  • GET  /health                                       │ │
│  │  • POST /api/set-baseline                            │ │
│  │  • POST /api/analyze                                 │ │
│  │  • POST /api/reset                                   │ │
│  └───────────────────────────────────────────────────────┘ │
│                         │                                   │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Audio Processing Pipeline                           │ │
│  │  ┌─────────────────────────────────────────────────┐ │ │
│  │  │ 1. RealtimeVoiceDetector                        │ │ │
│  │  │    • Feature extraction                         │ │ │
│  │  │    • MFCC computation                           │ │ │
│  │  │    • Spectral analysis                          │ │ │
│  │  │    • Phase discontinuity                        │ │ │
│  │  └─────────────────────────────────────────────────┘ │ │
│  │  ┌─────────────────────────────────────────────────┐ │ │
│  │  │ 2. RobustVoiceDetector                          │ │ │
│  │  │    • Identity verification (95% MFCC)           │ │ │
│  │  │    • AI detection (50% deviation)               │ │ │
│  │  │    • Confidence scoring                         │ │ │
│  │  │    • Risk assessment                            │ │ │
│  │  └─────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Set Baseline Flow
```
User uploads audio
       ↓
Frontend (streamlit_app.py)
       ↓
POST /api/set-baseline
       ↓
Backend API (api.py)
       ↓
Save to temp file
       ↓
RealtimeVoiceDetector.set_baseline()
       ↓
Extract features:
  • MFCC (13 coefficients)
  • Spectral centroid
  • Phase discontinuity
  • Zero crossing rate
       ↓
Store in memory (baseline_features)
       ↓
RobustVoiceDetector.set_baseline()
       ↓
Return success response
       ↓
Frontend updates session state
```

### 2. Analyze Voice Flow
```
User uploads test audio
       ↓
Frontend (streamlit_app.py)
       ↓
POST /api/analyze?strictness=normal
       ↓
Backend API (api.py)
       ↓
Save to temp file
       ↓
Load audio with soundfile
       ↓
RealtimeVoiceDetector.analyze_chunk()
       ↓
Extract test features
       ↓
RobustVoiceDetector.analyze()
       ↓
Compare features:
  ┌─────────────────────────────────┐
  │ Identity Check (MFCC)           │
  │ • Cosine similarity             │
  │ • Threshold: 95%                │
  │ • Result: is_authorized         │
  └─────────────────────────────────┘
  ┌─────────────────────────────────┐
  │ AI Detection (Phase/Spectral)   │
  │ • Deviation calculation         │
  │ • Threshold: 50%                │
  │ • Result: is_deepfake           │
  └─────────────────────────────────┘
       ↓
Calculate metrics:
  • Confidence score
  • Deviation percentage
  • Risk level
  • Verdict
       ↓
Return JSON response
       ↓
Frontend displays results
```

## Component Details

### Frontend (Streamlit)
```python
streamlit_app.py
├── Configuration
│   └── API_URL from secrets
├── Session State
│   └── baseline_set flag
├── UI Components
│   ├── Sidebar (settings, strictness)
│   ├── Column 1: Set Baseline
│   │   ├── Audio input/upload
│   │   └── Set signature button
│   └── Column 2: Test Voice
│       ├── Audio input/upload
│       └── Analyze button
└── API Calls
    ├── POST /api/set-baseline
    ├── POST /api/analyze
    └── POST /api/reset
```

### Backend (FastAPI)
```python
backend/api.py
├── FastAPI app
├── CORS middleware
├── Global state
│   ├── detector (RealtimeVoiceDetector)
│   ├── robust_detector (RobustVoiceDetector)
│   └── baseline_features
└── Endpoints
    ├── GET  / (info)
    ├── GET  /health
    ├── POST /api/set-baseline
    ├── POST /api/analyze
    └── POST /api/reset

backend/realtime_detector.py
├── RealtimeVoiceDetector class
├── set_baseline(audio_path)
├── analyze_chunk(audio, sr)
└── Feature extraction
    ├── MFCC (librosa)
    ├── Spectral centroid
    ├── Phase discontinuity
    └── Zero crossing rate

backend/robust_detector.py
├── RobustVoiceDetector class
├── set_baseline(features)
├── analyze(features, strictness)
└── Analysis logic
    ├── MFCC similarity (identity)
    ├── Phase deviation (AI detection)
    ├── Spectral deviation
    └── Confidence calculation
```

## Technology Stack

### Frontend
- **Framework**: Streamlit 1.54.0
- **HTTP Client**: requests
- **Audio**: audio-recorder-streamlit
- **Hosting**: Streamlit Cloud (free tier)

### Backend
- **Framework**: FastAPI 0.115.0
- **Server**: Uvicorn
- **Audio Processing**: librosa 0.11.0, soundfile 0.13.1
- **ML/Math**: numpy, scipy, scikit-learn
- **Hosting**: Render (free tier)

### Audio Processing
- **Sample Rate**: 16kHz (resampled)
- **Format**: WAV (mono)
- **Features**: MFCC (13), spectral, phase
- **Algorithms**: Cosine similarity, deviation analysis

## Security Architecture

```
┌─────────────────────────────────────┐
│  Frontend (Streamlit Cloud)        │
│  • HTTPS enforced                   │
│  • Secrets management               │
│  • No sensitive data storage        │
└────────────┬────────────────────────┘
             │ HTTPS
             ▼
┌─────────────────────────────────────┐
│  Backend (Render)                   │
│  • HTTPS enforced                   │
│  • CORS configured                  │
│  • Environment variables            │
│  • Temporary file cleanup           │
│  • No persistent storage            │
└─────────────────────────────────────┘
```

### Security Features
- ✅ HTTPS on both frontend and backend
- ✅ CORS protection
- ✅ Temporary file cleanup
- ✅ No persistent audio storage
- ✅ Environment variable secrets
- ✅ Input validation
- ⚠️ No authentication (add if needed)
- ⚠️ No rate limiting (add if needed)

## Scalability

### Current Capacity (Free Tier)
- **Concurrent Users**: ~10-20
- **Requests/Day**: ~1000
- **Audio Processing**: ~5-10 seconds per request
- **Storage**: Stateless (no database)

### Scaling Options

#### Horizontal Scaling
```
Load Balancer
     ├── Backend Instance 1
     ├── Backend Instance 2
     └── Backend Instance 3
```

#### Vertical Scaling
- Upgrade Render plan (more CPU/RAM)
- Optimize audio processing
- Add caching layer

#### Database Addition
```
Backend API
     ↓
PostgreSQL (Render)
     ├── User profiles
     ├── Voice signatures
     └── Analysis history
```

## Monitoring

### Health Checks
- **Backend**: `GET /health` every 30s
- **Frontend**: Streamlit built-in health
- **Render**: Automatic health monitoring

### Metrics to Track
- Request latency
- Error rates
- Cold start frequency
- Audio processing time
- Memory usage
- CPU usage

### Logging
- **Backend**: Uvicorn access logs
- **Frontend**: Streamlit logs
- **Render**: Centralized log viewer

## Cost Analysis

### Free Tier
```
Streamlit Cloud: $0/month
Render Backend:  $0/month (750 hrs)
─────────────────────────────
Total:           $0/month
```

### Production Tier
```
Streamlit Teams: $20/month (private apps)
Render Starter:  $7/month (no cold starts)
─────────────────────────────
Total:           $27/month
```

### Enterprise Tier
```
Streamlit Teams: $20/month
Render Standard: $25/month (better performance)
PostgreSQL:      $7/month (database)
─────────────────────────────
Total:           $52/month
```

## Deployment Environments

### Development
```
Local Machine
├── Backend: localhost:8000
├── Frontend: localhost:8501
└── Docker: docker-compose up
```

### Staging
```
Render (Free Tier)
├── Backend: staging-api.onrender.com
└── Frontend: staging-app.streamlit.app
```

### Production
```
Render (Paid Tier)
├── Backend: api.yourdomain.com
├── Frontend: app.yourdomain.com
└── Database: PostgreSQL on Render
```

## API Documentation

FastAPI provides automatic API documentation:
- **Swagger UI**: `https://your-api.onrender.com/docs`
- **ReDoc**: `https://your-api.onrender.com/redoc`
- **OpenAPI JSON**: `https://your-api.onrender.com/openapi.json`

## Future Enhancements

### Phase 1 (Current)
- ✅ Voice authentication
- ✅ AI detection
- ✅ Cloud deployment

### Phase 2 (Planned)
- [ ] User authentication
- [ ] Database integration
- [ ] Voice signature storage
- [ ] Analysis history

### Phase 3 (Future)
- [ ] Multi-language support
- [ ] Real-time streaming
- [ ] Mobile app
- [ ] Advanced analytics

---

This architecture provides a scalable, secure, and cost-effective solution for voice authentication with AI detection capabilities.
