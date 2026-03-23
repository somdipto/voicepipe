"""
VoicePipeline - Main orchestrator class
One-command STT + TTS for any app

Usage:
    from voicepipe import VoicePipeline
    voice = VoicePipeline()
    text = voice.speech_to_text("audio.wav")
    audio = voice.text_to_speech("Hello!")
"""
import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Union

logger = logging.getLogger("voicepipe")

DEFAULT_CACHE_DIR = os.path.expanduser("~/.voicepipe")


class VoicePipelineError(Exception):
    """VoicePipeline error."""
    pass


class VoicePipeline:
    """
    Main class for VoicePipe - one-command voice integration.
    
    Usage:
        from voicepipe import VoicePipeline
        voice = VoicePipeline()
        text = voice.speech_to_text("audio.wav")
        audio = voice.text_to_speech("Hello!")
    """
    
    def __init__(
        self,
        stt_model: str = "tiny",
        tts_backend: str = "gtts",
        tts_voice: str = "en",
        tts_speed: float = 1.0,
        language: str = "en",
        cache_dir: str = DEFAULT_CACHE_DIR,
    ):
        """
        Initialize VoicePipeline.
        
        Args:
            stt_model: whisper model (tiny, base, small)
            tts_backend: TTS backend (gtts, edge, pyttsx3)
            tts_voice: Voice/language
            tts_speed: Speech speed (0.5 - 2.0)
            language: STT language
            cache_dir: Model cache directory
        """
        self.stt_model = stt_model
        self.tts_backend = tts_backend
        self.tts_voice = tts_voice
        self.tts_speed = tts_speed
        self.language = language
        self.cache_dir = Path(cache_dir)
        
        # Components (lazy loaded)
        self._stt = None
        self._tts = None
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"VoicePipeline initialized (STT: {stt_model}, TTS: {tts_backend})")
    
    @property
    def stt(self):
        """Get STT engine (lazy init)."""
        if self._stt is None:
            from voicepipe.stt import STTEngine, check_stt_available
            
            # Check what's available first
            status = check_stt_available()
            
            if not status["whisper_found"]:
                raise VoicePipelineError(
                    "whisper-cli not found. Install from:\n"
                    "  https://github.com/ggerganov/whisper.cpp\n"
                    "Or: brew install whisper-cpp (macOS)"
                )
            
            if not status["ffmpeg_found"]:
                raise VoicePipelineError(
                    "FFmpeg not found. Install:\n"
                    "  macOS: brew install ffmpeg\n"
                    "  Linux: sudo apt install ffmpeg\n"
                    "  Windows: choco install ffmpeg"
                )
            
            if not status["model_found"]:
                logger.warning(
                    f"STT model not found at {self.cache_dir}/models.\n"
                    f"Will download on first use. Download models from:\n"
                    f"  https://huggingface.co/ggerganov/whisper.cpp/tree/main"
                )
            
            self._stt = STTEngine(
                model=self.stt_model,
                cache_dir=self.cache_dir,
                language=self.language,
            )
        
        return self._stt
    
    @property
    def tts(self):
        """Get TTS engine (lazy init)."""
        if self._tts is None:
            from voicepipe.tts import TTSEngine, check_tts_available
            
            status = check_tts_available()
            
            if not any(status.values()):
                raise VoicePipelineError(
                    "No TTS backend available. Install one of:\n"
                    "  pip install gtts        # Google TTS\n"
                    "  pip install edge-tts    # Microsoft Edge TTS\n"
                    "  pip install pyttsx3    # Offline system TTS"
                )
            
            self._tts = TTSEngine(
                model=self.tts_backend,
                voice=self.tts_voice,
                speed=self.tts_speed,
                cache_dir=self.cache_dir,
            )
        
        return self._tts
    
    # ========================================================================
    # STT Methods
    # ========================================================================
    
    def speech_to_text(self, audio_path: str) -> str:
        """
        Convert speech audio file to text.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
            
        Raises:
            VoicePipelineError: If STT fails
        """
        try:
            return self.stt.transcribe(audio_path)
        except Exception as e:
            raise VoicePipelineError(f"STT failed: {e}")
    
    def speech_to_text_bytes(self, audio_data: bytes) -> str:
        """
        Convert raw audio bytes to text.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Transcribed text
        """
        return self.stt.transcribe_bytes(audio_data)
    
    async def speech_to_text_async(self, audio_path: str) -> str:
        """Async version of speech_to_text."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.speech_to_text, audio_path)
    
    # ========================================================================
    # TTS Methods
    # ========================================================================
    
    def text_to_speech(self, text: str) -> bytes:
        """
        Convert text to speech audio.
        
        Args:
            text: Text to convert
            
        Returns:
            Audio bytes (WAV format)
            
        Raises:
            VoicePipelineError: If TTS fails
        """
        try:
            return self.tts.speak(text)
        except Exception as e:
            raise VoicePipelineError(f"TTS failed: {e}")
    
    def text_to_speech_file(self, text: str, output_path: str) -> str:
        """
        Convert text to speech and save to file.
        
        Args:
            text: Text to convert
            output_path: Output file path
            
        Returns:
            Path to saved file
        """
        return self.tts.speak_to_file(text, output_path)
    
    def list_voices(self) -> List[str]:
        """Get list of available TTS voices."""
        return self.tts.list_voices()
    
    async def text_to_speech_async(self, text: str) -> bytes:
        """Async version of text_to_speech."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.text_to_speech, text)
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def get_status(self) -> dict:
        """Get status of voice pipeline."""
        from voicepipe.stt import check_stt_available
        from voicepipe.tts import check_tts_available
        
        stt_status = check_stt_available()
        tts_status = check_tts_available()
        
        return {
            "stt_model": self.stt_model,
            "tts_backend": self.tts_backend,
            "tts_voice": self.tts_voice,
            "cache_dir": str(self.cache_dir),
            "whisper_available": stt_status["whisper_found"],
            "ffmpeg_available": stt_status["ffmpeg_found"],
            "stt_model_downloaded": stt_status["model_found"],
            "tts_backends": tts_status,
        }
    
    def cleanup(self):
        """Clean up resources."""
        self._stt = None
        self._tts = None


def create_voice_pipeline(**kwargs) -> VoicePipeline:
    """Create and return a VoicePipeline instance."""
    return VoicePipeline(**kwargs)