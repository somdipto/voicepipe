"""
STT Engine - whisper.cpp wrapper - FIXED VERSION

Fixed:
- Removed bare except statements
- Removed hardcoded paths
- Added input validation
- Better error handling
"""
import os
import subprocess
import logging
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger("voicepipe.stt")


class STTError(Exception):
    """STT error."""
    pass


class STTEngine:
    """Speech-to-Text engine using whisper.cpp."""
    
    MODELS = {
        "tiny": "ggml-tiny.en.bin",
        "base": "ggml-base.en.bin",
        "small": "ggml-small.bin",
    }
    
    def __init__(
        self,
        model: str = "tiny",
        cache_dir: Optional[Path] = None,
        language: str = "en",
    ):
        if model not in self.MODELS:
            raise STTError(f"Unknown model: {model}. Available: {list(self.MODELS.keys())}")
        
        self.model = model
        self.cache_dir = cache_dir or Path.home() / ".voicepipe" / "models"
        self.language = language
        self.model_path = None
        self.whisper_path = None
        
        self._find_whisper()
        self._ensure_model()
    
    def _find_whisper(self) -> None:
        """Find whisper CLI binary - portable path search."""
        import shutil
        
        search_paths = [
            self.cache_dir.parent / "whisper.cpp" / "build" / "bin" / "whisper-cli",
            Path.home() / "whisper.cpp" / "build" / "bin" / "whisper-cli",
            Path("/usr/local/bin/whisper-cli"),
            Path("/usr/bin/whisper-cli"),
        ]
        
        for p in search_paths:
            if p.exists():
                self.whisper_path = str(p)
                logger.info(f"Found whisper at: {self.whisper_path}")
                return
        
        # Check PATH using shutil.which (portable)
        path_whisper = shutil.which("whisper-cli")
        if path_whisper:
            self.whisper_path = path_whisper
            logger.info(f"Found whisper in PATH: {self.whisper_path}")
            return
        
        raise STTError(
            "whisper-cli not found. Install from:\n"
            "  https://github.com/ggerganov/whisper.cpp\n"
            "Or: brew install whisper-cpp (macOS)"
        )
    
    def _ensure_model(self) -> None:
        """Ensure model is downloaded."""
        model_file = self.MODELS.get(self.model)
        if not model_file:
            raise STTError(f"Unknown model: {self.model}")
        
        self.model_path = self.cache_dir / model_file
        
        if self.model_path.exists():
            logger.info(f"Model found: {self.model_path}")
            return
        
        # Try to download
        logger.info(f"Downloading model: {self.model}")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        urls = [
            f"https://huggingface.co/danon321/whisper.cpp-models/resolve/main/{model_file}",
            f"https://huggingface.co/ggerganov/whisper.cpp/resolve/main/{model_file}",
        ]
        
        for url in urls:
            try:
                result = subprocess.run(
                    ["curl", "-L", "-o", str(self.model_path), url],
                    capture_output=True,
                    timeout=300,
                )
                if result.returncode == 0 and self.model_path.exists():
                    logger.info(f"Model downloaded: {self.model_path}")
                    return
            except subprocess.TimeoutExpired:
                logger.warning(f"Download timed out for: {url}")
            except Exception as e:
                logger.warning(f"Download failed for {url}: {e}")
        
        raise STTError(
            f"Failed to download model. Please download manually from:\n"
            f"  https://huggingface.co/ggerganov/whisper.cpp/tree/main\n"
            f"Save as: {self.model_path}"
        )
    
    def transcribe(self, audio_path: str) -> str:
        """Transcribe audio file to text."""
        if not audio_path:
            raise STTError("Audio path cannot be empty")
        
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise STTError(f"Audio file not found: {audio_path}")
        
        # Convert to 16kHz mono WAV if needed
        converted_path = self._prepare_audio(audio_path)
        
        try:
            cmd = [
                self.whisper_path,
                "-m", str(self.model_path),
                "-f", str(converted_path),
                "-np",
            ]
            
            if self.language != "auto":
                cmd.extend(["-l", self.language])
            
            cmd.extend(["-otxt", "--no-timestamps"])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            if result.returncode != 0:
                # Try fallback
                cmd = [
                    self.whisper_path,
                    "-m", str(self.model_path),
                    "-f", str(converted_path),
                    "-np", "-l", self.language if self.language != "auto" else "en",
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                raise STTError(f"Transcription failed: {result.stderr}")
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise STTError("Transcription timed out - audio too long")
        except FileNotFoundError:
            raise STTError("whisper-cli not found")
        finally:
            # Cleanup temp file if we created one
            if converted_path != audio_path and converted_path.exists():
                try:
                    converted_path.unlink()
                except OSError as e:
                    logger.warning(f"Failed to cleanup {converted_path}: {e}")
    
    def _prepare_audio(self, audio_path: Path) -> Path:
        """Convert audio to 16kHz mono WAV if needed."""
        if audio_path.suffix.lower() == ".wav":
            return audio_path
        
        wav_path = audio_path.with_suffix(".wav")
        
        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", str(audio_path),
                    "-ar", "16000",
                    "-ac", "1",
                    "-c:a", "pcm_s16le",
                    str(wav_path),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                raise STTError(f"Audio conversion failed: {result.stderr}")
            
            return wav_path
        except subprocess.TimeoutExpired:
            raise STTError("Audio conversion timed out")
        except FileNotFoundError:
            raise STTError("FFmpeg not found. Install: brew install ffmpeg")
    
    def transcribe_bytes(self, audio_data: bytes) -> str:
        """Transcribe raw audio bytes."""
        if not audio_data:
            raise STTError("Audio data cannot be empty")
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name
        
        try:
            return self.transcribe(temp_path)
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass


def check_stt_available() -> dict:
    """Check if STT can be initialized."""
    import shutil
    
    result = {
        "whisper_found": False,
        "model_found": False,
        "ffmpeg_found": False,
    }
    
    # Check whisper using shutil.which (portable)
    if shutil.which("whisper-cli"):
        result["whisper_found"] = True
    
    # Check ffmpeg
    if shutil.which("ffmpeg"):
        result["ffmpeg_found"] = True
    
    # Check default model
    cache_dir = Path.home() / ".voicepipe" / "models"
    if (cache_dir / "ggml-tiny.en.bin").exists():
        result["model_found"] = True
    
    return result
