"""
TTS Engine - Kittentts Only

Lightweight, offline, local TTS for VoicePipe
"""
import os
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger("voicepipe.tts")


class TTSError(Exception):
    """TTS error."""
    pass


class TTSEngine:
    """Text-to-Speech engine using Kittentts."""
    
    # Available voices
    VOICES = ["Bella", "Jasper", "Luna", "Bruno", "Rosie", "Hugo", "Kiki", "Leo"]
    
    def __init__(
        self,
        voice: str = "Jasper",
        speed: float = 1.0,
        cache_dir: Optional[Path] = None,
    ):
        if not voice:
            raise TTSError("Voice cannot be empty")
        if not 0.5 <= speed <= 2.0:
            raise TTSError("Speed must be between 0.5 and 2.0")
        
        self.voice = voice if voice in self.VOICES else "Jasper"
        self.speed = speed
        self.cache_dir = cache_dir or Path.home() / ".voicepipe"
        
        self._model = None
        self._init_model()
    
    def _init_model(self) -> None:
        """Initialize Kittentts model."""
        try:
            from kittentts import KittenTTS
            
            # Use nano model - smallest (25MB) and fastest
            self._model = KittenTTS("KittenML/kitten-tts-nano-0.8-int8")
            logger.info(f"KittenTTS loaded with voice: {self.voice}")
            
        except ImportError:
            raise TTSError(
                "KittenTTS not installed. Install with:\n"
                "  pip install Kittentts\n"
                "  apt-get install espeak-ng"
            )
        except Exception as e:
            raise TTSError(f"Failed to load Kittentts: {e}")
    
    def speak(self, text: str) -> bytes:
        """Convert text to speech audio."""
        if not text or not text.strip():
            raise TTSError("Text cannot be empty")
        
        try:
            # Generate audio
            audio = self._model.generate(
                text, 
                voice=self.voice,
                speed=self.speed
            )
            
            # Convert numpy array to bytes (16-bit PCM)
            import numpy as np
            audio_int16 = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
            
            return audio_int16.tobytes()
            
        except Exception as e:
            raise TTSError(f"TTS failed: {e}")
    
    def speak_to_file(self, text: str, output_path: str) -> str:
        """Save TTS to file."""
        if not text or not text.strip():
            raise TTSError("Text cannot be empty")
        if not output_path:
            raise TTSError("Output path cannot be empty")
        
        audio = self.speak(text)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write WAV file
        import wave
        with wave.open(str(output_path), 'wb') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(24000)
            f.writeframes(audio)
        
        return str(output_path)
    
    @staticmethod
    def list_voices() -> list:
        """List available voices."""
        return list(TTSEngine.VOICES)


def check_tts_available() -> dict:
    """Check if TTS is available."""
    result = {"kittentts": False}
    
    try:
        from kittentts import KittenTTS
        result["kittentts"] = True
    except ImportError:
        pass
    
    return result