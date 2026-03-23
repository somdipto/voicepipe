"""
TTS Engine - Text to Speech

Supports multiple backends:
1. gTTS (Google TTS) - requires internet, free
2. pyttsx3 - offline, system TTS
3. edge-tts - Microsoft Edge TTS, free, good quality
"""
import os
import subprocess
import logging
import wave
import io
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("voicepipe.tts")

# Available voices for each backend
GTTS_VOICES = ["en"]  # Single language, accent varies

# Edge TTS voices
EDGE_VOICES = {
    "en": ["en-US-AriaNeural", "en-US-GuyNeural", "en-US-JennyNeural"],
    "en-GB": ["en-GB-SoniaNeural", "en-GB-RyanNeural"],
}


class TTSEngine:
    """
    Text-to-Speech engine with multiple backend support.
    
    Usage:
        from voicepipe.tts import TTSEngine
        tts = TTSEngine()
        audio = tts.speak("Hello world")
    """
    
    def __init__(
        self,
        model: str = "gtts",  # gtts, pyttsx3, edge
        voice: str = "en",
        speed: float = 1.0,
        cache_dir: Optional[Path] = None,
    ):
        """
        Initialize TTS engine.
        
        Args:
            model: Backend to use (gtts, pyttsx3, edge)
            voice: Voice/language code
            speed: Speech speed (0.5 - 2.0)
            cache_dir: Directory for caching
        """
        self.model = model
        self.voice = voice
        self.speed = speed
        self.cache_dir = cache_dir or Path.home() / ".voicepipe"
        self.backend = None
        
        # Initialize backend
        self._init_backend()
    
    def _init_backend(self):
        """Initialize TTS backend."""
        backends = ["gtts", "edge", "pyttsx3"]
        
        for backend in backends:
            try:
                if backend == "gtts":
                    from gtts import gTTS
                    self.backend = "gtts"
                    logger.info("Using gTTS backend")
                    return
                elif backend == "edge":
                    from edge_tts import Communicate
                    self.backend = "edge"
                    logger.info("Using edge-tts backend")
                    return
                elif backend == "pyttsx3":
                    import pyttsx3
                    engine = pyttsx3.init()
                    self.backend = "pyttsx3"
                    self._pyttsx3_engine = engine
                    logger.info("Using pyttsx3 backend")
                    return
            except ImportError:
                continue
        
        raise RuntimeError(
            "No TTS backend available. Install one of:\n"
            "  pip install gtts        # Google TTS (online)\n"
            "  pip install edge-tts    # Microsoft Edge TTS (online)\n"
            "  pip install pyttsx3     # Offline system TTS"
        )
    
    def speak(self, text: str) -> bytes:
        """
        Convert text to speech audio.
        
        Args:
            text: Text to convert
            
        Returns:
            Audio bytes (WAV format, 16kHz, 16-bit mono)
        """
        if self.backend == "gtts":
            return self._speak_gtts(text)
        elif self.backend == "edge":
            return self._speak_edge(text)
        elif self.backend == "pyttsx3":
            return self._speak_pyttsx3(text)
        else:
            raise RuntimeError(f"Unknown backend: {self.backend}")
    
    def _speak_gtts(self, text: str) -> bytes:
        """Use Google TTS."""
        from gtts import gTTS
        
        try:
            tts = gTTS(text=text, lang=self.voice.split("-")[0])
            
            # Save to temp mp3
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                mp3_path = f.name
            
            tts.save(mp3_path)
            
            # Convert to WAV
            wav_path = mp3_path.replace(".mp3", ".wav")
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", mp3_path, "-ar", "16000", "-ac", "1", wav_path],
                capture_output=True,
            )
            
            with open(wav_path, "rb") as f:
                audio = f.read()
            
            # Cleanup
            try:
                os.unlink(mp3_path)
                os.unlink(wav_path)
            except:
                pass
            
            return audio
            
        except Exception as e:
            raise RuntimeError(f"gTTS failed: {e}")
    
    def _speak_edge(self, text: str) -> bytes:
        """Use Microsoft Edge TTS."""
        from edge_tts import Communicate
        
        try:
            # Get voice
            voices = EDGE_VOICES.get(self.voice, EDGE_VOICES["en"])
            voice = voices[0]
            
            # Generate
            import asyncio
            import tempfile
            
            async def generate():
                communicate = Communicate(text, voice)
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    mp3_path = f.name
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        with open(mp3_path, "ab") as f:
                            f.write(chunk["data"])
                return mp3_path
            
            mp3_path = asyncio.run(generate())
            
            # Convert to WAV
            wav_path = mp3_path.replace(".mp3", ".wav")
            subprocess.run(
                ["ffmpeg", "-y", "-i", mp3_path, "-ar", "16000", "-ac", "1", wav_path],
                capture_output=True,
            )
            
            with open(wav_path, "rb") as f:
                audio = f.read()
            
            # Cleanup
            try:
                os.unlink(mp3_path)
                os.unlink(wav_path)
            except:
                pass
            
            return audio
            
        except Exception as e:
            raise RuntimeError(f"edge-tts failed: {e}")
    
    def _speak_pyttsx3(self, text: str) -> bytes:
        """Use pyttsx3 (offline)."""
        import pyttsx3
        
        try:
            engine = pyttsx3.init()
            
            # Set properties
            engine.setProperty("rate", int(150 * self.speed))
            engine.setProperty("voice", self.voice)
            
            # Save to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                wav_path = f.name
            
            engine.save_to_file(text, wav_path)
            engine.runAndWait()
            
            with open(wav_path, "rb") as f:
                audio = f.read()
            
            try:
                os.unlink(wav_path)
            except:
                pass
            
            return audio
            
        except Exception as e:
            raise RuntimeError(f"pyttsx3 failed: {e}")
    
    def speak_to_file(self, text: str, output_path: str) -> str:
        """Save TTS to file."""
        audio = self.speak(text)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with wave.open(str(output_path), "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(16000)
            # Skip WAV header, write raw PCM
            # Find where audio data starts (44 bytes for WAV header)
            if audio[:4] == b"RIFF":
                # Has WAV header, skip to data
                f.write(audio[44:])
            else:
                f.write(audio)
        
        return str(output_path)
    
    def list_voices(self) -> List[str]:
        """List available voices."""
        if self.backend == "gtts":
            return ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
        elif self.backend == "edge":
            result = []
            for lang, voices in EDGE_VOICES.items():
                result.extend(voices)
            return result
        elif self.backend == "pyttsx3":
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            return [v.id for v in voices]
        return []


def check_tts_available() -> dict:
    """Check which TTS backends are available."""
    backends = {"gtts": False, "edge": False, "pyttsx3": False}
    
    try:
        import gtts
        backends["gtts"] = True
    except:
        pass
    
    try:
        import edge_tts
        backends["edge"] = True
    except:
        pass
    
    try:
        import pyttsx3
        backends["pyttsx3"] = True
    except:
        pass
    
    return backends