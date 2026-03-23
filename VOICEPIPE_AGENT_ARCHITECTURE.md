# VoicePipe Agent Architecture v2

## Problem Statement

Current VoicePipe requires:
- Manual whisper.cpp installation
- Manual model download
- Manual FFmpeg installation
- Manual TTS backend installation

**Goal:** One command to rule them all.

---

## Solution: VoicePipe Agent

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      VoicePipe Agent                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Installer  │    │    Agent     │    │   Manager    │  │
│  │   Engine    │    │   Loop       │    │   (State)    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Auto-Install Pipeline                     │   │
│  │  1. Detect missing dependencies                        │   │
│  │  2. Download/install automatically                    │   │
│  │  3. Verify and report status                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Voice Pipeline                              │   │
│  │  STT (whisper.cpp) ←→ Agent ←→ TTS (multi-backend)   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Components

#### 1. Installer Engine
- Auto-detect OS (Mac/Linux/Windows)
- Auto-install FFmpeg
- Auto-install/build whisper.cpp
- Auto-download models
- Auto-install TTS backends

#### 2. Agent Loop
- Continuous voice interaction
- Context memory
- Tool execution
- Multi-step tasks

#### 3. State Manager
- Track installation status
- Cache models
- Manage API keys
- Persist settings

---

## Implementation Plan

### Phase 1: Universal Installer

```python
class AutoInstaller:
    """One-command install everything."""
    
    def install_all(self) -> bool:
        """Install all dependencies automatically."""
        # 1. Install FFmpeg
        # 2. Install whisper.cpp (binary or from source)
        # 3. Download models
        # 4. Install TTS backends
        
    def check_status(self) -> dict:
        """Check what's installed."""
        
    def install_missing(self) -> dict:
        """Install only what's missing."""
```

### Phase 2: Agent Mode

```python
class VoiceAgent:
    """Continuous voice agent."""
    
    async def run(self):
        """Run agent loop."""
        while True:
            # Listen
            audio = await self.listen()
            
            # Understand
            intent = await self.understand(audio)
            
            # Execute
            result = await self.execute(intent)
            
            # Respond
            await self.speak(result)
```

### Phase 3: Unified API

```python
from voicepipe import VoiceAgent

# One command - installs everything automatically
agent = VoiceAgent()
await agent.run()  # Start voice agent

# Or use directly
voice = VoicePipeline()
voice.ensure_installed()  # Auto-install everything
text = voice.speech_to_text("audio.wav")  # Works!
```

---

## Code Implementation

### Auto-Installer

```python
import subprocess
import platform
import os
import sys

class AutoInstaller:
    """Automatic installation for all dependencies."""
    
    def __init__(self):
        self.os = platform.system().lower()
        self.home = os.path.expanduser("~")
        self.cache = os.path.join(self.home, ".voicepipe")
        
    def install_all(self, force: bool = False) -> dict:
        """Install all dependencies."""
        results = {}
        
        # 1. FFmpeg
        results["ffmpeg"] = self.install_ffmpeg()
        
        # 2. TTS Backends
        results["tts"] = self.install_tts_backends()
        
        # 3. STT (whisper.cpp)
        results["stt"] = self.install_whisper()
        
        # 4. Models
        results["models"] = self.download_models()
        
        return results
    
    def install_ffmpeg(self) -> dict:
        """Install FFmpeg."""
        if self.os == "darwin":
            return self._brew_install("ffmpeg")
        elif self.os == "linux":
            return self._apt_install("ffmpeg")
        elif self.os == "windows":
            return self._choco_install("ffmpeg")
        return {"status": "unknown_os"}
    
    def install_whisper(self) -> dict:
        """Install whisper.cpp."""
        whisper_dir = os.path.join(self.cache, "whisper.cpp")
        
        if os.path.exists(whisper_dir):
            return {"status": "already_installed"}
        
        # Clone and build
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", 
                 "https://github.com/ggerganov/whisper.cpp.git", 
                 whisper_dir],
                capture_output=True, timeout=120
            )
            
            # Build
            subprocess.run(["make", "whisper-cli"], 
                         cwd=whisper_dir, capture_output=True)
            
            return {"status": "installed", "path": whisper_dir}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def download_models(self) -> dict:
        """Download whisper models."""
        models_dir = os.path.join(self.cache, "models")
        os.makedirs(models_dir, exist_ok=True)
        
        # Download tiny model
        model_url = "https://huggingface.co/danon321/whisper.cpp-models/resolve/main/ggml-tiny.en.bin"
        model_path = os.path.join(models_dir, "ggml-tiny.en.bin")
        
        if os.path.exists(model_path):
            return {"status": "already_exists"}
        
        try:
            subprocess.run(
                ["curl", "-L", "-o", model_path, model_url],
                capture_output=True, timeout=300
            )
            return {"status": "downloaded", "path": model_path}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def check_status(self) -> dict:
        """Check installation status."""
        return {
            "ffmpeg": self._check_command("ffmpeg"),
            "whisper": os.path.exists(os.path.join(self.cache, "whisper.cpp", "whisper-cli")),
            "model": os.path.exists(os.path.join(self.cache, "models", "ggml-tiny.en.bin")),
            "gtts": self._check_python_module("gtts"),
            "edge_tts": self._check_python_module("edge_tts"),
        }
    
    def _check_command(self, cmd: str) -> bool:
        result = subprocess.run(["which", cmd], capture_output=True)
        return result.returncode == 0
    
    def _check_python_module(self, module: str) -> bool:
        return subprocess.run(
            [sys.executable, "-c", f"import {module}"],
            capture_output=True
        ).returncode == 0
```

---

## Usage

### One-Command Setup

```bash
# Install everything automatically
pip install voicepipe[agent]
voicepipe install  # Downloads and installs all dependencies
```

### Start Voice Agent

```bash
# Start the voice agent
voicepipe agent
```

### Python API

```python
from voicepipe import VoiceAgent

# First run - auto-installs everything
agent = VoiceAgent()

# Start listening
await agent.run()

# Or use directly
voice = agent.voice
voice.speech_to_text("hello.wav")  # Just works!
voice.text_to_speech("Hello!")      # Just works!
```

---

## File Structure

```
voicepipe/
├── src/voicepipe/
│   ├── __init__.py          # Main exports
│   ├── voice_agent.py       # Agent implementation
│   ├── installer.py         # Auto-installer
│   ├── pipeline.py         # Voice pipeline
│   ├── stt/
│   │   ├── __init__.py
│   │   ├── whisper.py      # whisper.cpp wrapper
│   │   └── fastwhisper.py  # Faster-Whisper alternative
│   └── tts/
│       ├── __init__.py
│       ├── gtts.py
│       ├── edge.py
│       └── pyttsx3.py
├── cli.py
└── pyproject.toml
```

---

## Installation Flow

```
User: pip install voicepipe[agent]
         ↓
    Auto-install FFmpeg (if missing)
         ↓
    Auto-install TTS backends
         ↓
    Auto-clone whisper.cpp (if missing)
         ↓
    Auto-download models (if missing)
         ↓
    Ready to use!
```

---

## Success Metrics

- [ ] One command install works on Mac
- [ ] One command install works on Linux
- [ ] One command install works on Windows
- [ ] STT works after fresh install
- [ ] TTS works after fresh install
- [ ] Agent mode works
- [ ] Tests pass