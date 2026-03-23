"""
TTS Engine - Text to Speech - FIXED VERSION

Fixed:
- Removed all bare except: statements
- Added proper error handling
- Added input validation
"""
import os
import subprocess
import logging
import wave
import io
from pathlib import Path
from typing import List, Optional, Dict

logger = logging.getLogger("voicepipe.tts")

# Voice configurations
EDGE_VOICES: Dict[str, List[str]] = {
    "en": ["en-US-AriaNeural", "en-US-GuyNeural", "en-US-JennyNeural"],
    "en-GB": ["en-GB-SoniaNeural", "en-GB-RyanNeural"],
}


class TTSError(Exception):
    """TTS error."""
    pass


class TTSEngine:
    """Text-to-Speech engine with multiple backend support."""
    
    def __init__(
        self,
        model: str = "gtts",
        voice: str = "en",
        speed: float = 1.0,
        cache_dir: Optional[Path] = None,
    ):
        if not voice:
            raise TTSError("Voice cannot be empty")
        if not 0.1 <= speed <= 3.0:
            raise TTSError("Speed must be between 0.1 and 3.0")
        
        self.model = model
        self.voice = voice
        self.speed = speed
        self.cache_dir = cache_dir or Path.home() / ".voicepipe"
        self.backend: Optional[str] = None
        self._pyttsx3_engine = None
        
        self._init_backend()
    
    def _init_backend(self) -> None:
        """Initialize TTS backend with proper error handling."""
        backends = [
            ("gtts", self._check_gtts),
            ("edge", self._check_edge),
            ("pyttsx3", self._check_pyttsx3),
        ]
        
        for backend_name, check_func in backends:
            try:
                if check_func():
                    self.backend = backend_name
                    logger.info(f"Using {backend_name} backend")
                    return
            except Exception as e:
                logger.warning(f"Backend {backend_name} failed: {e}")
                continue
        
        raise TTSError(
            "No TTS backend available. Install one of:\n"
            "  pip install gtts\n"
            "  pip install edge-tts\n"
            "  pip install pyttsx3"
        )
    
    def _check_gtts(self) -> bool:
        """Check if gTTS is available."""
        import gtts  # noqa: F401
        return True
    
    def _check_edge(self) -> bool:
        """Check if edge-tts is available."""
        import edge_tts  # noqa: F401
        return True
    
    def _check_pyttsx3(self) -> bool:
        """Check if pyttsx3 is available."""
        import pyttsx3
        return True
    
    def speak(self, text: str) -> bytes:
        """Convert text to speech audio."""
        if not text or not text.strip():
            raise TTSError("Text cannot be empty")
        
        if self.backend == "gtts":
            return self._speak_gtts(text)
        elif self.backend == "edge":
            return self._speak_edge(text)
        elif self.backend == "pyttsx3":
            return self._speak_pyttsx3(text)
        else:
            raise TTSError(f"Unknown backend: {self.backend}")
    
    def _speak_gtts(self, text: str) -> bytes:
        """Use Google TTS."""
        from gtts import gTTS
        
        if not text:
            raise TTSError("Text cannot be empty")
        
        try:
            tts = gTTS(text=text, lang=self.voice.split("-")[0])
            
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                mp3_path = f.name
            
            tts.save(mp3_path)
            
            # Convert to WAV
            wav_path = mp3_path.replace(".mp3", ".wav")
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", mp3_path, "-ar", "16000", "-ac", "1", wav_path],
                capture_output=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                raise TTSError(f"FFmpeg conversion failed: {result.stderr.decode()}")
            
            with open(wav_path, "rb") as f:
                audio = f.read()
            
            # Cleanup
            for path in [mp3_path, wav_path]:
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except OSError as e:
                        logger.warning(f"Failed to cleanup {path}: {e}")
            
            return audio
            
        except subprocess.TimeoutExpired:
            raise TTSError("TTS conversion timed out")
        except ImportError as e:
            raise TTSError(f"gTTS not installed: {e}")
        except Exception as e:
            raise TTSError(f"gTTS failed: {e}")
    
    def _speak_edge(self, text: str) -> bytes:
        """Use Microsoft Edge TTS."""
        from edge_tts import Communicate
        
        if not text:
            raise TTSError("Text cannot be empty")
        
        try:
            voices = EDGE_VOICES.get(self.voice, EDGE_VOICES["en"])
            voice = voices[0]
            
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
                timeout=30,
            )
            
            with open(wav_path, "rb") as f:
                audio = f.read()
            
            # Cleanup
            for path in [mp3_path, wav_path]:
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except OSError as e:
                        logger.warning(f"Failed to cleanup {path}: {e}")
            
            return audio
            
        except ImportError as e:
            raise TTSError(f"edge-tts not installed: {e}")
        except asyncio.TimeoutError:
            raise TTSError("Edge TTS timed out")
        except Exception as e:
            raise TTSError(f"edge-tts failed: {e}")
    
    def _speak_pyttsx3(self, text: str) -> bytes:
        """Use pyttsx3 (offline)."""
        import pyttsx3
        
        if not text:
            raise TTSError("Text cannot be empty")
        
        try:
            if self._pyttsx3_engine is None:
                self._pyttsx3_engine = pyttsx3.init()
            
            engine = self._pyttsx3_engine
            engine.setProperty("rate", int(150 * self.speed))
            
            # Try to set voice
            try:
                voices = engine.getProperty("voices")
                if voices:
                    engine.setProperty("voice", voices[0].id)
            except Exception:
                pass  # Continue without specific voice
            
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                wav_path = f.name
            
            engine.save_to_file(text, wav_path)
            engine.runAndWait()
            
            with open(wav_path, "rb") as f:
                audio = f.read()
            
            if wav_path and os.path.exists(wav_path):
                try:
                    os.unlink(wav_path)
                except OSError as e:
                    logger.warning(f"Failed to cleanup {wav_path}: {e}")
            
            return audio
            
        except ImportError as e:
            raise TTSError(f"pyttsx3 not installed: {e}")
        except Exception as e:
            raise TTSError(f"pyttsx3 failed: {e}")
    
    def speak_to_file(self, text: str, output_path: str) -> str:
        """Save TTS to file."""
        if not text or not text.strip():
            raise TTSError("Text cannot be empty")
        if not output_path:
            raise TTSError("Output path cannot be empty")
        
        audio = self.speak(text)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with wave.open(str(output_path), "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(16000)
            if audio[:4] == b"RIFF":
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
            try:
                import pyttsx3
                engine = pyttsx3.init()
                voices = engine.getProperty("voices")
                return [v.id for v in voices]
            except Exception:
                return []
        return []


def check_tts_available() -> Dict[str, bool]:
    """Check which TTS backends are available."""
    backends = {"gtts": False, "edge": False, "pyttsx3": False}
    
    try:
        import gtts
        backends["gtts"] = True
    except ImportError:
        pass
    
    try:
        import edge_tts
        backends["edge"] = True
    except ImportError:
        pass
    
    try:
        import pyttsx3
        backends["pyttsx3"] = True
    except ImportError:
        pass
    
    return backends
