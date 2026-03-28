"""VoicePipe TTS - Text to Speech with auto-detection."""

import subprocess
import tempfile
import os
import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger("voicepipe.tts")

# Backend priority order
_BACKENDS = ["edge-tts", "gtts", "pyttsx3", "espeak-ng"]


def detect_tts() -> Optional[str]:
    """Auto-detect best available TTS backend."""
    for backend in _BACKENDS:
        try:
            if backend == "edge-tts":
                import edge_tts
                return "edge-tts"
            elif backend == "gtts":
                import gtts
                return "gtts"
            elif backend == "pyttsx3":
                import pyttsx3
                return "pyttsx3"
            elif backend == "espeak-ng":
                subprocess.run(["espeak-ng", "--version"], capture_output=True, check=True)
                return "espeak-ng"
        except (ImportError, FileNotFoundError, subprocess.CalledProcessError):
            continue
    return None


class TTS:
    """Text-to-Speech with auto-detected backend."""
    
    def __init__(self, backend: Optional[str] = None, voice: str = "en", **kwargs):
        self.backend = backend or detect_tts()
        self.voice = voice
        
        if not self.backend:
            raise ImportError(
                "No TTS backend found. Run:\n"
                "  pip install voicepipe[build]\n"
                "Or: voicepipe install"
            )
    
    def speak(self, text: str) -> bytes:
        """Convert text to speech audio bytes."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        if self.backend == "edge-tts":
            return self._speak_edge(text)
        elif self.backend == "gtts":
            return self._speak_gtts(text)
        elif self.backend == "pyttsx3":
            return self._speak_pyttsx3(text)
        elif self.backend == "espeak-ng":
            return self._speak_espeak(text)
        
        raise RuntimeError(f"Unknown backend: {self.backend}")
    
    def _speak_edge(self, text: str) -> bytes:
        """Edge TTS (Microsoft)."""
        import edge_tts
        import asyncio
        
        async def generate():
            comm = edge_tts.Communicate(text, "en-US-AriaNeural")
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                mp3 = f.name
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    with open(mp3, "ab") as f:
                        f.write(chunk["data"])
            return mp3
        
        mp3_path = asyncio.run(generate())
        
        try:
            wav_path = mp3_path.replace(".mp3", ".wav")
            subprocess.run(
                ["ffmpeg", "-y", "-i", mp3_path, "-ar", "16000", "-ac", "1", wav_path],
                capture_output=True, timeout=30,
            )
            with open(wav_path, "rb") as f:
                return f.read()
        finally:
            for p in [mp3_path, wav_path]:
                if p and os.path.exists(p):
                    os.unlink(p)
    
    def _speak_gtts(self, text: str) -> bytes:
        """Google TTS."""
        from gtts import gTTS
        
        tts = gTTS(text=text, lang=self.voice.split("-")[0])
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            mp3 = f.name
        
        tts.save(mp3)
        
        try:
            wav = mp3.replace(".mp3", ".wav")
            subprocess.run(
                ["ffmpeg", "-y", "-i", mp3, "-ar", "16000", "-ac", "1", wav],
                capture_output=True, timeout=30,
            )
            with open(wav, "rb") as f:
                return f.read()
        finally:
            for p in [mp3, wav]:
                if p and os.path.exists(p):
                    os.unlink(p)
    
    def _speak_pyttsx3(self, text: str) -> bytes:
        """pyttsx3 (offline)."""
        import pyttsx3
        
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav = f.name
        
        engine.save_to_file(text, wav)
        engine.runAndWait()
        
        try:
            with open(wav, "rb") as f:
                return f.read()
        finally:
            os.unlink(wav)
    
    def _speak_espeak(self, text: str) -> bytes:
        """espeak-ng (offline)."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav = f.name
        
        subprocess.run(
            ["espeak-ng", "-w", wav, text],
            capture_output=True, timeout=30,
        )
        
        try:
            with open(wav, "rb") as f:
                return f.read()
        finally:
            os.unlink(wav)
    
    def save(self, text: str, output_path: str) -> str:
        """Save TTS to file."""
        audio = self.speak(text)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(audio)
        
        return str(output_path)
    
    def list_voices(self) -> List[str]:
        """List available voices."""
        if self.backend == "edge-tts":
            return ["en-US-AriaNeural", "en-US-GuyNeural", "en-US-JennyNeural"]
        elif self.backend == "gtts":
            return ["en", "es", "fr", "de", "it", "pt"]
        elif self.backend == "pyttsx3":
            return ["default"]
        elif self.backend == "espeak-ng":
            return ["en", "en-us", "en-gb"]
        return []