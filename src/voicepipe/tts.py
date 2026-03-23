"""
TTS Engine - KittenTTS wrapper
"""
import os
import subprocess
import logging
import wave
import numpy as np
from pathlib import Path
from typing import List

logger = logging.getLogger("voicepipe.tts")

# KittenTTS model configurations
KITTEN_MODELS = {
    "nano": {
        "name": "KittenML/kitten-tts-nano-0.8-int8",
        "size": "25 MB",
        "params": "15M",
    },
    "micro": {
        "name": "KittenML/kitten-tts-micro-0.8",
        "size": "41 MB",
        "params": "40M",
    },
    "mini": {
        "name": "KittenML/kitten-tts-mini-0.8",
        "size": "80 MB",
        "params": "80M",
    },
}

AVAILABLE_VOICES = ["Bella", "Jasper", "Luna", "Bruno", "Rosie", "Hugo", "Kiki", "Leo"]


class TTSEngine:
    """
    Text-to-Speech engine using KittenTTS.
    """
    
    def __init__(
        self,
        model: str = "nano",
        voice: str = "Bella",
        speed: float = 1.0,
        cache_dir: Path = None,
    ):
        """
        Initialize TTS engine.
        
        Args:
            model: Model size (nano, micro, mini)
            voice: Voice name
            speed: Speech speed (0.5 - 2.0)
            cache_dir: Directory to cache models
        """
        self.model = model
        self.voice = voice
        self.speed = speed
        self.cache_dir = cache_dir or Path.home() / ".voicepipe"
        self.tts_model = None
        
        # Validate voice
        if voice not in AVAILABLE_VOICES:
            raise ValueError(f"Unknown voice: {voice}. Available: {AVAILABLE_VOICES}")
        
        # Validate model
        if model not in KITTEN_MODELS:
            raise ValueError(f"Unknown model: {model}. Available: {list(KITTEN_MODELS.keys())}")
        
        # Initialize
        self._init_model()
    
    def _init_model(self):
        """Initialize KittenTTS model."""
        # Try importing KittenTTS
        try:
            from kittentts import KittenTTS
            
            model_name = KITTEN_MODELS[self.model]["name"]
            logger.info(f"Loading KittenTTS model: {model_name}")
            
            self.tts_model = KittenTTS(model_name)
            logger.info("KittenTTS loaded successfully")
            
        except ImportError:
            logger.warning("KittenTTS not installed, using fallback")
            self.tts_model = None
            
            # Try gTTS as fallback
            try:
                from gtts import gTTS
                self._fallback = "gtts"
                logger.info("Using gTTS fallback")
            except ImportError:
                raise RuntimeError(
                    "Neither KittenTTS nor gTTS available. "
                    "Install with: pip install kittentts gtts"
                )
        except Exception as e:
            logger.error(f"Failed to load KittenTTS: {e}")
            raise
    
    def speak(self, text: str) -> bytes:
        """
        Convert text to speech audio.
        
        Args:
            text: Text to convert
            
        Returns:
            Audio bytes (WAV format, 24kHz, 16-bit)
        """
        if self.tts_model:
            return self._speak_kittentts(text)
        elif hasattr(self, '_fallback') and self._fallback == "gtts":
            return self._speak_gtts(text)
        else:
            raise RuntimeError("No TTS engine available")
    
    def _speak_kittentts(self, text: str) -> bytes:
        """Use KittenTTS to generate speech."""
        try:
            # Generate audio
            audio = self.tts_model.generate(text, voice=self.voice, speed=self.speed)
            
            # Convert to WAV bytes
            return self._audio_to_wav(audio)
            
        except Exception as e:
            logger.error(f"KittenTTS generation failed: {e}")
            raise RuntimeError(f"TTS generation failed: {e}")
    
    def _speak_gtts(self, text: str) -> bytes:
        """Use gTTS as fallback."""
        from gtts import gTTS
        
        tts = gTTS(text)
        
        # Save to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_path = f.name
        
        try:
            tts.save(temp_path)
            
            # Convert to WAV
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wf:
                wav_path = wf.name
            
            subprocess.run(
                ["ffmpeg", "-y", "-i", temp_path, "-ar", "24000", "-ac", "1", wav_path],
                check=True,
                capture_output=True,
            )
            
            with open(wav_path, "rb") as f:
                audio_bytes = f.read()
            
            os.unlink(temp_path)
            os.unlink(wav_path)
            
            return audio_bytes
            
        except FileNotFoundError:
            raise RuntimeError("FFmpeg not found for audio conversion")
    
    def _audio_to_wav(self, audio: np.ndarray) -> bytes:
        """Convert numpy audio to WAV bytes."""
        # Convert to 16-bit
        audio_int16 = (audio * 32767).astype(np.int16)
        
        # Create WAV in memory
        import io
        
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as f:
            f.setnchannels(1)  # Mono
            f.setsampwidth(2)  # 16-bit
            f.setframerate(24000)  # 24kHz
            f.writeframes(audio_int16.tobytes())
        
        return buffer.getvalue()
    
    def speak_to_file(self, text: str, output_path: str) -> str:
        """
        Convert text to speech and save to file.
        
        Args:
            text: Text to convert
            output_path: Path to save audio
            
        Returns:
            Path to saved file
        """
        audio = self.speak(text)
        
        # Save as WAV
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with wave.open(str(output_path), 'wb') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(24000)
            
            # Convert audio to 16-bit and write
            if isinstance(audio, bytes):
                # Already WAV, just write
                # Need to extract data
                import io
                with wave.open(io.BytesIO(audio), 'rb') as wf:
                    frames = wf.readframes(wf.getnframes())
                    f.writeframes(frames)
            else:
                audio_int16 = (audio * 32767).astype(np.int16)
                f.writeframes(audio_int16.tobytes())
        
        return str(output_path)
    
    def list_voices(self) -> List[str]:
        """Get list of available voices."""
        if self.tts_model and hasattr(self.tts_model, 'available_voices'):
            return self.tts_model.available_voices
        return AVAILABLE_VOICES
    
    def get_available_models(self) -> dict:
        """Get information about available models."""
        return KITTEN_MODELS