"""
VoicePipeline - One-command voice for any app

Usage:
    from voicepipe import VoicePipeline
    
    # Auto-installs everything on first run
    voice = VoicePipeline()
    
    # STT
    text = voice.speech_to_text("audio.wav")
    
    # TTS  
    audio = voice.text_to_speech("Hello!")
"""
import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger("voicepipe")

DEFAULT_CACHE_DIR = os.path.expanduser("~/.voicepipe")


class VoicePipelineError(Exception):
    """VoicePipeline error."""
    pass


class VoicePipeline:
    """
    One-command voice integration.
    
    Auto-installs everything on first use.
    
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
        auto_install: bool = True,
    ):
        self.stt_model = stt_model
        self.tts_backend = tts_backend
        self.tts_voice = tts_voice
        self.tts_speed = tts_speed
        self.language = language
        self.cache_dir = Path(cache_dir)
        self.auto_install = auto_install
        
        self._stt = None
        self._tts = None
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Check status on init
        if auto_install:
            self._ensure_ready()
    
    def _ensure_ready(self):
        """Ensure all dependencies are installed."""
        try:
            from voicepipe.installer import AutoInstaller
            installer = AutoInstaller(str(self.cache_dir))
            status = installer.check_status()
            
            missing = []
            if not status.get("ffmpeg"):
                missing.append("ffmpeg")
            if not status.get("whisper"):
                missing.append("whisper")
            if not status.get("model"):
                missing.append("model")
            
            if missing:
                logger.warning(f"Missing: {missing}. Run voice.install() to install.")
        except Exception as e:
            logger.warning(f"Could not check status: {e}")
    
    def install(self, force: bool = False) -> dict:
        """
        Install all dependencies automatically.
        
        Args:
            force: Reinstall even if already installed
            
        Returns:
            dict: Installation results
        """
        from voicepipe.installer import AutoInstaller
        installer = AutoInstaller(str(self.cache_dir))
        return installer.install_all(force=force)
    
    def check_status(self) -> dict:
        """Check installation status."""
        from voicepipe.installer import AutoInstaller
        installer = AutoInstaller(str(self.cache_dir))
        return installer.check_status()
    
    @property
    def stt(self):
        """Get STT engine."""
        if self._stt is None:
            from voicepipe.stt import STTEngine
            
            # Check for whisper
            from voicepipe.installer import AutoInstaller
            installer = AutoInstaller(str(self.cache_dir))
            whisper_path = installer.get_whisper_path()
            
            if not Path(whisper_path).exists() and not Path(whisper_path.replace("whisper-cli", "build/bin/whisper-cli")).exists():
                if self.auto_install:
                    logger.info("Installing whisper.cpp...")
                    result = installer.install_whisper()
                    if result.get("status") != "installed":
                        raise VoicePipelineError("Could not install whisper. Run voice.install()")
                else:
                    raise VoicePipelineError(
                        "whisper-cli not found. Run voice.install() or set auto_install=True"
                    )
            
            self._stt = STTEngine(
                model=self.stt_model,
                cache_dir=self.cache_dir / "models",
                language=self.language,
            )
        
        return self._stt
    
    @property
    def tts(self):
        """Get TTS engine."""
        if self._tts is None:
            from voicepipe.tts import TTSEngine
            self._tts = TTSEngine(
                model=self.tts_backend,
                voice=self.tts_voice,
                speed=self.tts_speed,
                cache_dir=self.cache_dir,
            )
        return self._tts
    
    def speech_to_text(self, audio_path: str) -> str:
        """
        Convert speech to text.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        try:
            return self.stt.transcribe(audio_path)
        except Exception as e:
            raise VoicePipelineError(f"STT failed: {e}")
    
    def speech_to_text_bytes(self, audio_data: bytes) -> str:
        """Convert raw audio bytes to text."""
        return self.stt.transcribe_bytes(audio_data)
    
    def text_to_speech(self, text: str) -> bytes:
        """
        Convert text to speech.
        
        Args:
            text: Text to convert
            
        Returns:
            Audio bytes
        """
        try:
            return self.tts.speak(text)
        except Exception as e:
            raise VoicePipelineError(f"TTS failed: {e}")
    
    def text_to_speech_file(self, text: str, output_path: str) -> str:
        """Save TTS to file."""
        return self.tts.speak_to_file(text, output_path)
    
    def list_voices(self) -> List[str]:
        """List available voices."""
        return self.tts.list_voices()
    
    def get_status(self) -> dict:
        """Get pipeline status."""
        return {
            "stt_model": self.stt_model,
            "tts_backend": self.tts_backend,
            "tts_voice": self.tts_voice,
            "cache_dir": str(self.cache_dir),
            **self.check_status(),
        }
    
    def cleanup(self):
        """Clean up resources."""
        self._stt = None
        self._tts = None


# For convenience
def create_voice_pipeline(**kwargs) -> VoicePipeline:
    """Create VoicePipeline instance."""
    return VoicePipeline(**kwargs)
