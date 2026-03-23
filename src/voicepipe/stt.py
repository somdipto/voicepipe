"""
STT Engine - whisper.cpp wrapper
"""
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("voicepipe.stt")

# Whisper model URLs (GGML format)
MODEL_URLS = {
    "tiny": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin",
    "base": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin",
    "small": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
    "medium": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin",
    "large": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin",
}

# Map model names to file names
MODEL_FILES = {
    "tiny": "ggml-tiny.en.bin",
    "base": "ggml-base.en.bin",
    "small": "ggml-small.bin",
    "medium": "ggml-medium.bin",
    "large": "ggml-large-v3.bin",
}


class STTEngine:
    """
    Speech-to-Text engine using whisper.cpp.
    """
    
    def __init__(
        self,
        model: str = "tiny",
        cache_dir: Path = None,
        language: str = "en",
    ):
        """
        Initialize STT engine.
        
        Args:
            model: Model size (tiny, base, small, medium, large)
            cache_dir: Directory to cache models
            language: Language code or "auto"
        """
        self.model = model
        self.cache_dir = cache_dir or Path.home() / ".voicepipe"
        self.language = language
        self.model_path = None
        
        # Find or download whisper binary
        self._find_whisper()
        
        # Download model if needed
        self._ensure_model()
    
    def _find_whisper(self):
        """Find whisper CLI binary."""
        # Check common locations
        paths = [
            self.cache_dir / "whisper.cpp" / "build" / "bin" / "whisper-cli",
            self.cache_dir / "whisper-cli",
            Path("/usr/local/bin/whisper-cli"),
            Path("/usr/bin/whisper-cli"),
            Path.home() / "whisper.cpp" / "build" / "bin" / "whisper-cli",
        ]
        
        for p in paths:
            if p.exists():
                self.whisper_path = str(p)
                logger.info(f"Found whisper at: {self.whisper_path}")
                return
        
        # Check if in PATH
        result = subprocess.run(["which", "whisper-cli"], capture_output=True)
        if result.returncode == 0:
            self.whisper_path = result.stdout.decode().strip()
            logger.info(f"Found whisper in PATH: {self.whisper_path}")
            return
        
        # Not found - will try to use system whisper or error
        self.whisper_path = "whisper-cli"
        logger.warning("whisper-cli not found, will try PATH")
    
    def _ensure_model(self):
        """Ensure model is downloaded."""
        model_file = MODEL_FILES.get(self.model, f"ggml-{self.model}.bin")
        self.model_path = self.cache_dir / "models" / model_file
        
        if self.model_path.exists():
            logger.info(f"Model found: {self.model_path}")
            return
        
        # Download model
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Downloading model: {self.model}")
        
        url = MODEL_URLS.get(self.model)
        if not url:
            raise ValueError(f"Unknown model: {self.model}")
        
        # Download using curl
        result = subprocess.run(
            ["curl", "-L", "-o", str(self.model_path), url],
            capture_output=True,
            timeout=600,
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to download model: {result.stderr.decode()}")
        
        logger.info(f"Model downloaded: {self.model_path}")
    
    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Run whisper
        cmd = [
            self.whisper_path,
            "-m", str(self.model_path),
            "-f", audio_path,
            "-np",  # No prints (just output)
        ]
        
        if self.language != "auto":
            cmd.extend(["-l", self.language])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            if result.returncode != 0:
                # Try with --no-gpu flag
                cmd.append("--no-gpu")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise TimeoutError("Transcription timeout - audio too long")
        except FileNotFoundError:
            raise RuntimeError(
                "whisper-cli not found. Install: "
                "https://github.com/ggerganov/whisper.cpp"
            )
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}")
    
    def transcribe_bytes(self, audio_data: bytes) -> str:
        """Transcribe raw audio bytes."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name
        
        try:
            return self.transcribe(temp_path)
        finally:
            os.unlink(temp_path)