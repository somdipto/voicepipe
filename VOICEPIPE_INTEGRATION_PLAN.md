# VoicePipe - STT/TTS Wrapper for AI Product Stack

## The Vision

VoicePipe should be the **easy-to-integrate voice layer** that AI companies plug into their product:

```
AI Copilot / ChatGPT / Agent → VoicePipe → End User
              ↑                         ↑
        Provides text               Speaks output
        Receives voice
```

**The Goal:** Make it dead simple for any AI product to add voice.

---

## What AI Companies Need

| Need | Why |
|------|-----|
| **Simple API** | 2-3 function calls to add voice |
| **Streaming** | Real-time conversation (no lag) |
| **Provider agnostic** | Swap TTS/STT providers easily |
| **Format standardization** | Audio in → Audio out (they handle LLM) |
| **Low latency** | <300ms for natural conversation |
| **Self-hosted option** | No dependency on external APIs |

---

## Architecture Design

### The Core Interface (What We Build)

```python
from voicepipe import VoicePipeline

# Initialize
voice = VoicePipeline()

# STT: Audio → Text (returns text, they send to their LLM)
text = voice.speech_to_text(audio_bytes)

# TTS: Text → Audio (takes LLM response, plays to user)
audio = voice.text_to_speech(llm_response)
```

### Provider Abstraction Layer

```python
# Users can swap backends
voice = VoicePipeline(
    stt_provider="whisper",      # or "deepgram", "assemblyai"
    tts_provider="edge",         # or "elevenlabs", "coqui"
)
```

### Streaming Interface (Future)

```python
# For real-time conversation
async for text in voice.stream_listen():
    # Send to LLM
    response = await llm.chat(text)
    await voice.stream_speak(response)
```

---

## Implementation Plan

### Phase 1: Clean API Wrapper (NOW)

**Goal:** Make the current STT/TTS easy to integrate

- [ ] Simplify VoicePipeline to 2 main methods
- [ ] Add provider configuration
- [ ] Standardize audio format (16kHz, mono, 16-bit)
- [ ] Add clear error messages
- [ ] Document the API

### Phase 2: Multi-Provider Support (NEXT)

**Goal:** Let users choose their providers

- [ ] Add TTS provider interface:
  - [ ] gTTS (default, free)
  - [ ] Edge TTS (Microsoft, free)
  - [ ] ElevenLabs (optional, paid)
  - [ ] Coqui (self-hosted option)
- [ ] Add STT provider interface:
  - [ ] whisper.cpp (default, local)
  - [ ] Deepgram API (optional)
  - [ ] AssemblyAI API (optional)

### Phase 3: Streaming (LATER)

**Goal:** Real-time voice conversation

- [ ] Streaming STT (chunked transcription)
- [ ] Streaming TTS (progressive audio)
- [ ] Audio buffer management

### Phase 4: Production Features

- [ ] Webhook system for events
- [ ] Audio normalization
- [ ] Latency benchmarks
- [ ] Language detection

---

## The Simple API

```python
# === INSTALL ===
# pip install voicepipe

# === USAGE ===
from voicepipe import VoicePipeline
voice = VoicePipeline()

# 1. Get text from audio (they send to their LLM)
text = voice.speech_to_text(audio_data)

# 2. Play their LLM response
voice.speak(llm_response)

# === DONE ===
# They handle the LLM, we handle the voice
```

---

## Competitor Analysis

| Product | STT | TTS | Self-Hosted | Price |
|---------|-----|-----|-------------|-------|
| **VoicePipe** | ✅ | ✅ | ✅ | Free |
| ElevenLabs | ❌ | ✅ | ❌ | Paid |
| Deepgram | ✅ | ❌ | ❌ | Paid |
| Coqui | ✅ | ✅ | ✅ | Free |

**VoicePipe advantage:** Full stack + free + self-hosted

---

## Implementation Priority

### MUST HAVE (Phase 1):
1. Clean 2-method API
2. Standard audio format
3. Provider config
4. Good docs

### SHOULD HAVE (Phase 2):
1. ElevenLabs TTS provider
2. Deepgram STT provider option

### NICE TO HAVE (Phase 3):
1. Streaming
2. Webhooks

---

*This becomes the "voice layer" for any AI product.*
