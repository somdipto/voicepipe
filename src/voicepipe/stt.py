"""
STT Engine - whisper.cpp wrapper

IMPORTANT: This module requires:
1. whisper-cli binary installed (from whisper.cpp)
2. Models downloaded to ~/.voicepipe/models/
3. FFmpeg for audio conversion
"""
import os
import subprocess
import logging
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger("voicepipe.stt")


class STTEngine:
    """
    Speech-to-Text engine using whisper.cpp.
    
    Usage:
        from voicepipe.stt import STTEngine
        stt = STTEngine()
        text = stt.transcribe("audio.wav")
    """
    
    # Mapping from model names to ggml model files
    MODELS = {
        "tiny": "ggml-tiny.en.bin",
        "base": "ggml-base.en.bin", 
        "small": "ggml-small.bin",
        "medium": "ggml-medium.bin",
        "large": "ggml-large-v3.bin",
    }
    
    # HuggingFace URLs for models
    MODEL_URLS = {
        "tiny": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin",
        "base": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin",
        "small": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
        "medium": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin",
        "large": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin",
    }
    
    def __init__(
        self,
        model: str = "tiny",
        cache_dir: Optional[Path] = None,
        language: str = "en",
    ):
        """
        Initialize STT engine.
        
        Args:
            model: Model size (tiny, base, small, medium, large)
            cache_dir: Directory to cache models (default: ~/.voicepipe)
            language: Language code (en, es, fr, etc.) or "auto"
        """
        self.model = model
        self.cache_dir = cache_dir or Path.home() / ".voicepipe" / "models"
        self.language = language
        self.model_path = None
        self.whisper_path = None
        
        # Initialize
        self._find_whisper()
        self._ensure_model()
    
    def _find_whisper(self):
        """Find whisper CLI binary."""
        # Common locations
        search_paths = [
            self.cache_dir.parent / "whisper.cpp" / "build" / "bin" / "whisper-cli",
            Path.home() / "whisper.cpp" / "build" / "bin" / "whisper-cli",
            Path("/root/whisper.cpp/build/bin/whisper-cli"),
            Path("/usr/local/bin/whisper-cli"),
            Path("/usr/bin/whisper-cli"),
        ]
        
        for p in search_paths:
            if p.exists():
                self.whisper_path = str(p)
                logger.info(f"Found whisper at: {self.whisper_path}")
                return
        
        # Check if it's in PATH
        result = subprocess.run(["which", "whisper-cli"], capture_output=True)
        if result.returncode == 0:
            self.whisper_path = result.stdout.decode().strip()
            logger.info(f"Found whisper in PATH: {self.whisper_path}")
            return
        
        raise RuntimeError(
            "whisper-cli not found. Install from: https://github.com/ggerganov/whisper.cpp\n"
            "Or run: brew install whisper-cpp (macOS)"
        )
    
    def _ensure_model(self):
        """Ensure model is downloaded."""
        model_file = self.MODELS.get(self.model)
        if not model_file:
            raise ValueError(f"Unknown model: {self.model}. Available: {list(self.MODELS.keys())}")
        
        self.model_path = self.cache_dir / model_file
        
        if self.model_path.exists():
            logger.info(f"Model found: {self.model_path}")
            return
        
        # Need to download
        logger.info(f"Downloading model: {self.model} ({model_file})")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        url = self.MODEL_URLS.get(self.model)
        if not url:
            raise RuntimeError(f"No URL for model: {self.model}")
        
        logger.info(f"Downloading from: {url}")
        
        result = subprocess.run(
            ["curl", "-L", "-o", str(self.model_path), url],
            capture_output=True,
            timeout=600,
        )
        
        if result.returncode != 0:
            # Try alternative URL format
            alt_url = f"https://huggingface.co/danon321/whisper.cpp-models/resolve/main/{model_file}"
            logger.info(f"Trying alternative URL: {alt_url}")
            result = subprocess.run(
                ["curl", "-L", "-o", str(self.model_path), alt_url],
                capture_output=True,
                timeout=600,
            )
        
        if result.returncode != 0 or not self.model_path.exists():
            raise RuntimeError(
                f"Failed to download model. Please download manually from:\n"
                f"https://huggingface.co/ggerganov/whisper.cpp/tree/main\n"
                f"Save as: {self.model_path}"
            )
        
        logger.info(f"Model downloaded: {self.model_path}")
    
    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file (wav, mp3, ogg, m4a, etc.)
            
        Returns:
            Transcribed text
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If transcription fails
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Convert to 16kHz mono WAV if needed
        converted_path = self._prepare_audio(audio_path)
        
        try:
            # Build command
            cmd = [
                self.whisper_path,
                "-m", str(self.model_path),
                "-f", str(converted_path),
                "-np",  # No prints except result
            ]
            
            if self.language != "auto":
                cmd.extend(["-l", self.language])
            
            # Add common options for better accuracy
            cmd.extend(["-otxt", "--no-timestamps"])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            if result.returncode != 0:
                # Try without extra options
                cmd = [
                    self.whisper_path,
                    "-m", str(self.model_path),
                    "-f", str(converted_path),
                    "-np",
                    "-l", self.language if self.language != "auto" else "en",
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                raise RuntimeError(f"Transcription failed: {result.stderr}")
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise TimeoutError("Transcription timeout - audio too long")
        finally:
            # Clean up temp file if we created one
            if converted_path != audio_path and converted_path.exists():
                try:
                    converted_path.unlink()
                except:
                    pass
    
    def _prepare_audio(self, audio_path: Path) -> Path:
        """Convert audio to 16kHz mono WAV if needed."""
        if audio_path.suffix.lower() == ".wav":
            # Check if it's already 16kHz mono
            # For now, just return as-is
            return audio_path
        
        # Need to convert
        wav_path = audio_path.with_suffix(".wav")
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(audio_path),
            "-ar", "16000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            str(wav_path),
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Audio conversion failed: {result.stderr}")
        
        return wav_path
    
    def transcribe_bytes(self, audio_data: bytes) -> str:
        """Transcribe raw audio bytes."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name
        
        try:
            return self.transcribe(temp_path)
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass


# Helper to check if STT is available
def check_stt_available() -> dict:
    """Check if STT can be initialized."""
    result = {
        "whisper_found": False,
        "model_found": False,
        "ffmpeg_found": False,
    }
    
    # Check whisper
    r = subprocess.run(["which", "whisper-cli"], capture_output=True)
    if r.returncode == 0:
        result["whisper_found"] = True
    
    # Check ffmpeg
    r = subprocess.run(["which", "ffmpeg"], capture_output=True)
    if r.returncode == 0:
        result["ffmpeg_found"] = True
    
    # Check default model
    cache_dir = Path.home() / ".voicepipe" / "models"
    if (cache_dir / "ggml-tiny.en.bin").exists():
        result["model_found"] = True
    
    return result