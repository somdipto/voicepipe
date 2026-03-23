# VoicePipe - Universal Voice Pipeline PRD

## Product Requirement Document: One-Command Voice Integration for Any App

---

## 1. Executive Summary

**Product Name:** VoicePipe  
**Type:** Developer SDK / Python Package  
**Core Functionality:** One-command integration of STT (whisper.cpp) + TTS (KittenTTS) into any application  
**Target Users:** Developers building chatbots, voice assistants, and AI apps who need voice I/O

---

## 2. Problem Statement

### Current State
- Every chatbot developer rebuilds voice from scratch
- STT and TTS require separate implementations
- Complex setup (FFmpeg, models, ONNX, etc.)
- No standardized API across apps

### Developer Pain Points
1. **Setup complexity** - 10+ steps to get voice working
2. **Model management** - Download, cache, update models
3. **Platform differences** - Works differently on Mac/Linux/Windows
4. **Audio processing** - Format conversion, sample rates, etc.
5. **No single solution** - Must combine multiple tools

---

## 3. Solution: VoicePipe

**One command to rule them all:**
```bash
pip install voicepipe
```

**One line to add voice to any app:**
```python
from voicepipe import VoicePipeline

voice = VoicePipeline()  # Auto-downloads models
text = voice.speech_to_text("audio.wav")
audio = voice.text_to_speech("Hello!")
```

---

## 4. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        VoicePipe SDK                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     │
│  │   STT API   │     │   TTS API   │     │  Audio Utils│     │
│  │  (whisper)  │     │ (KittenTTS) │     │ (ffmpeg,etc)│     │
│  └─────────────┘     └─────────────┘     └─────────────┘     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Model Manager (auto-download, cache)        │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Responsibility |
|-----------|----------------|
| **VoicePipeline** | Main class, orchestrates everything |
| **STT Engine** | whisper.cpp wrapper |
| **TTS Engine** | KittenTTS wrapper |
| **ModelManager** | Auto-download, cache, version management |
| **AudioUtils** | Format conversion, sample rate normalization |
| **Config** | Single config file for all settings |

---

## 5. API Design

### Basic Usage
```python
from voicepipe import VoicePipeline

# Initialize (auto-downloads models)
voice = VoicePipeline()

# Speech to Text
text = voice.speech_to_text("audio.wav")
# OR with raw bytes
text = voice.speech_to_text_bytes(audio_data)

# Text to Speech
audio_data = voice.text_to_speech("Hello, world!")
# OR save to file
voice.text_to_speech("Hello!", output_file="output.wav")

# Get available voices
voices = voice.list_voices()
```

### Advanced Configuration
```python
voice = VoicePipeline(
    stt_model="tiny",        # tiny, base, small
    tts_model="nano",        # nano, micro, mini
    tts_voice="Bella",       # 8 voices available
    tts_speed=1.0,           # 0.5 - 2.0
    language="en",           # auto-detect if None
    cache_dir="~/.voicepipe" # model cache location
)
```

### Async Support
```python
# For high-performance apps
text = await voice.speech_to_text_async("audio.wav")
audio = await voice.text_to_speech_async("Hello!")
```

### Streaming (Real-time)
```python
# For live conversations
async for text in voice.stream_speech(microphone_stream):
    print(f"User said: {text}")

# Stream TTS output
async for chunk in voice.stream_text_to_speech("Long response..."):
    audio_player.play(chunk)
```

---

## 6. Supported Platforms

| Platform | Status | Notes |
|----------|--------|-------|
| **macOS** | ✅ Full | Apple Silicon + Intel |
| **Linux** | ✅ Full | x86, ARM (Raspberry Pi) |
| **Windows** | ✅ Full | x64 |
| **iOS** | 🔄 Soon | Swift wrapper |
| **Android** | 🔄 Soon | Gradle plugin |

---

## 7. Model Options

### STT (whisper.cpp)
| Model | Size | RAM | Speed | Use Case |
|-------|------|-----|-------|----------|
| **tiny** | 75MB | ~500MB | 10x realtime | Fastest, lowest accuracy |
| **base** | 142MB | ~1GB | 5x realtime | Balanced |
| **small** | 466MB | ~2GB | 2x realtime | Better accuracy |

**Recommendation for most apps:** `tiny` (fastest, good enough)

### TTS (KittenTTS)
| Model | Size | Params | Speed | Quality |
|-------|------|--------|-------|---------|
| **nano** | 25MB | 15M | Very Fast | Good |
| **micro** | 41MB | 40M | Fast | Better |
| **mini** | 80MB | 80M | Fast | Best |

**Recommendation for most apps:** `nano` (smallest, fast, good quality)

---

## 8. Technical Requirements

### Runtime
- Python 3.8+
- FFmpeg (system dependency)
- 2GB+ disk space for models

### Optional
- GPU: CUDA (faster STT), Metal (Mac), Vulkan

---

## 9. Installation & Setup

### One Command Install
```bash
pip install voicepipe
```

### Auto-Setup (First Run)
```python
from voicepipe import VoicePipeline

voice = VoicePipeline()  # Downloads ~100MB models automatically
# Done! Ready to use
```

### Docker Support
```dockerfile
FROM python:3.11-slim
RUN pip install voicepipe
CMD python -c "from voicepipe import VoicePipeline; v=VoicePipeline(); print(v.text_to_speech('Hello!'))"
```

---

## 10. Use Cases

### Chatbots
```python
# Add voice to any chatbot
@app.post("/voice/chat")
async def voice_chat(audio: bytes):
    text = voice.speech_to_text_bytes(audio)
    response = await chatbot.chat(text)
    audio_response = voice.text_to_speech(response)
    return {"audio": audio_response}
```

### Voice Assistants
```python
# Continuous voice interaction
async def run_assistant():
    async for user_text in voice.stream_speech(microphone):
        response = await assistant.respond(user_text)
        voice.text_to_speech(response, play=True)
```

### Accessibility
```python
# Convert text to speech for accessibility
voice.text_to_speech(long_article, output_file="article.mp3")
```

---

## 11. Roadmap

### Phase 1 (MVP)
- [x] whisper.cpp + KittenTTS integration
- [x] Basic sync API
- [x] Model auto-download
- [ ] PyPI release
- [ ] Documentation

### Phase 2 (Enhanced)
- [ ] Async/streaming support
- [ ] Multiple language support
- [ ] Voice customization API

### Phase 3 (Platform)
- [ ] Mobile SDKs (iOS, Android)
- [ ] WebAssembly version
- [ ] Real-time streaming

---

## 12. Competitive Analysis

| Product | STT | TTS | One-Command | Free |
|---------|-----|-----|-------------|------|
| **VoicePipe** | ✅ | ✅ | ✅ | ✅ |
| ElevenLabs API | ❌ | ✅ | ❌ | ❌ (paid) |
| Whisper API | ✅ | ❌ | ❌ | ❌ (paid) |
| Coqui TTS | ✅ | ✅ | ❌ | ✅ (complex) |
| Azure Speech | ✅ | ✅ | ❌ | ❌ (paid) |

**VoicePipe advantage:** Completely free + one-command + local (no API calls)

---

## 13. Monetization (Optional)

### Free Tier
- Full local voice (no limits)
- Community support

### Paid Tier (Optional)
- Cloud-hosted models (faster)
- Custom voice cloning
- Enterprise support
- Managed hosting

---

## 14. Success Metrics

1. **Installs** - Target: 10,000+ installs in first year
2. **GitHub Stars** - Target: 1,000+ stars
3. **Use Cases** - Integrate into 50+ apps
4. **Performance** - <100ms latency for TTS, <500ms for STT

---

## 15. Next Steps

1. Create GitHub repo: `danlab-ai/voicepipe`
2. Build MVP package
3. Publish to PyPI
4. Create documentation site
5. Developer outreach

---

**Document Version:** 1.0  
**Created:** March 2026  
**Author:** DanLab  
**Status:** Ready for Development