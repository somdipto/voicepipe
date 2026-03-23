"""
VoicePipeline - Main orchestrator class
"""
import os
import asyncio
import subprocess
import logging
from pathlib import Path
from typing import Optional, List, Union

logger = logging.getLogger("voicepipe")

DEFAULT_CACHE_DIR = os.path.expanduser("~/.voicepipe")


class VoicePipeline:
    """
    Main class for VoicePipe - one-command voice integration.
    
    Usage:
        from voicepipe import VoicePipeline
        voice = VoicePipeline()  # Auto-downloads models
        text = voice.speech_to_text("audio.wav")
        audio = voice.text_to_speech("Hello!")
    """
    
    def __init__(
        self,
        stt_model: str = "tiny",
        tts_model: str = "nano",
        tts_voice: str = "Bella",
        tts_speed: float = 1.0,
        language: str = "en",
        cache_dir: str = DEFAULT_CACHE_DIR,
        auto_download: bool = True,
    ):
        """
        Initialize VoicePipeline.
        
        Args:
            stt_model: whisper.cpp model (tiny, base, small)
            tts_model: KittenTTS model (nano, micro, mini)
            tts_voice: Voice name (Bella, Jasper, Luna, etc.)
            tts_speed: Speech speed (0.5 - 2.0)
            language: Language code (en, etc.) or "auto"
            cache_dir: Directory to cache models
            auto_download: Auto-download models if not found
        """
        self.stt_model = stt_model
        self.tts_model = tts_model
        self.tts_voice = tts_voice
        self.tts_speed = tts_speed
        self.language = language
        self.cache_dir = Path(cache_dir)
        
        # Initialize components
        self._stt = None
        self._tts = None
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"VoicePipeline initialized (STT: {stt_model}, TTS: {tts_model})")
        
    def _init_stt(self):
        """Lazy init STT engine."""
        if self._stt is None:
            from voicepipe.stt import STTEngine
            self._stt = STTEngine(
                model=self.stt_model,
                cache_dir=self.cache_dir,
                language=self.language,
            )
        return self._stt
    
    def _init_tts(self):
        """Lazy init TTS engine."""
        if self._tts is None:
            from voicepipe.tts import TTSEngine
            self._tts = TTSEngine(
                model=self.tts_model,
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
            audio_path: Path to audio file (wav, mp3, ogg, etc.)
            
        Returns:
            Transcribed text
        """
        # Ensure audio is in correct format
        audio_path = self._prepare_audio(audio_path)
        
        # Run STT
        stt = self._init_stt()
        return stt.transcribe(audio_path)
    
    def speech_to_text_bytes(self, audio_data: bytes) -> str:
        """
        Convert raw audio bytes to text.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Transcribed text
        """
        # Save to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name
        
        try:
            return self.speech_to_text(temp_path)
        finally:
            os.unlink(temp_path)
    
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
            text: Text to convert to speech
            
        Returns:
            Audio bytes (WAV format, 24kHz)
        """
        tts = self._init_tts()
        return tts.speak(text)
    
    def text_to_speech_file(self, text: str, output_path: str) -> str:
        """
        Convert text to speech and save to file.
        
        Args:
            text: Text to convert
            output_path: Path to save audio file
            
        Returns:
            Path to saved file
        """
        tts = self._init_tts()
        return tts.speak_to_file(text, output_path)
    
    def list_voices(self) -> List[str]:
        """
        Get list of available TTS voices.
        
        Returns:
            List of voice names
        """
        tts = self._init_tts()
        return tts.list_voices()
    
    async def text_to_speech_async(self, text: str) -> bytes:
        """Async version of text_to_speech."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.text_to_speech, text)
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def _prepare_audio(self, audio_path: str) -> str:
        """Ensure audio is in correct format for processing."""
        path = Path(audio_path)
        
        # Check if file exists
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Convert to 16kHz mono WAV if needed
        if path.suffix.lower() not in ['.wav']:
            # Need to convert
            wav_path = path.with_suffix('.wav')
            self._convert_audio(str(path), str(wav_path), sample_rate=16000, mono=True)
            return str(wav_path)
        
        return str(audio_path)
    
    def _convert_audio(
        self, 
        input_path: str, 
        output_path: str, 
        sample_rate: int = 16000,
        mono: bool = True
    ):
        """Convert audio using FFmpeg."""
        import subprocess
        
        mono_arg = "-ac 1" if mono else ""
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-ar", str(sample_rate),
            mono_arg,
            "-c:a", "pcm_s16le",
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg conversion failed: {e.stderr.decode()}")
            raise RuntimeError(f"Audio conversion failed: {e}")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg not found. Install: brew install ffmpeg")
    
    def get_status(self) -> dict:
        """Get status of voice pipeline."""
        return {
            "stt_model": self.stt_model,
            "tts_model": self.tts_model,
            "tts_voice": self.tts_voice,
            "cache_dir": str(self.cache_dir),
            "stt_ready": self._stt is not None,
            "tts_ready": self._tts is not None,
        }
    
    def cleanup(self):
        """Clean up resources."""
        self._stt = None
        self._tts = None
        logger.info("VoicePipeline cleaned up")


# Convenience function
def create_voice_pipeline(**kwargs) -> VoicePipeline:
    """Create and return a VoicePipeline instance."""
    return VoicePipeline(**kwargs)