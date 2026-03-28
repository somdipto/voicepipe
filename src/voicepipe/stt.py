"""VoicePipe STT - Speech to Text with auto-detection."""

import subprocess
import tempfile
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("voicepipe.stt")

# Backend priority order
_BACKENDS = ["faster-whisper", "whisper-cli", "api"]


def detect_stt() -> Optional[str]:
    """Auto-detect best available STT backend."""
    for backend in _BACKENDS:
        try:
            if backend == "faster-whisper":
                import faster_whisper
                return "faster-whisper"
            elif backend == "whisper-cli":
                result = subprocess.run(["which", "whisper-cli"], capture_output=True)
                if result.returncode == 0:
                    return "whisper-cli"
            elif backend == "api":
                # API backend always available
                return "api"
        except (ImportError, FileNotFoundError):
            continue
    return None


class STT:
    """Speech-to-Text with auto-detected backend."""
    
    def __init__(self, backend: Optional[str] = None, model: str = "base", **kwargs):
        self.backend = backend or detect_stt()
        self.model = model
        
        if not self.backend:
            raise ImportError(
                "No STT backend found. Run:\n"
                "  pip install voicepipe[build]\n"
                "Or: voicepipe install"
            )
        
        self._model = None
        self._init_backend()
    
    def _init_backend(self):
        """Initialize the detected backend."""
        if self.backend == "faster-whisper":
            import faster_whisper
            self._model = faster_whisper.FasterWhisper(
                model_size_or_path=self.model,
                device="cpu",
                compute_type="int8",
            )
        elif self.backend == "whisper-cli":
            # Find whisper-cli
            whisper_path = None
            for check in [
                Path.home() / ".voicepipe" / "whisper.cpp" / "build" / "bin" / "whisper-cli",
                Path.home() / "whisper.cpp" / "build" / "bin" / "whisper-cli",
            ]:
                if check.exists():
                    whisper_path = check
                    break
            
            if not whisper_path:
                result = subprocess.run(["which", "whisper-cli"], capture_output=True)
                if result.returncode == 0:
                    whisper_path = Path(result.stdout.strip())
            
            if not whisper_path.exists():
                raise RuntimeError("whisper-cli not found. Run: voicepipe install")
            
            self._whisper_path = whisper_path
        
        elif self.backend == "api":
            # Try whisper-cli as fallback
            whisper_path = None
            for check in [
                Path.home() / ".voicepipe" / "whisper.cpp" / "build" / "bin" / "whisper-cli",
                Path.home() / "whisper.cpp" / "build" / "bin" / "whisper-cli",
            ]:
                if check.exists():
                    whisper_path = check
                    break
            
            if whisper_path:
                self.backend = "whisper-cli"
                self._whisper_path = whisper_path
            else:
                raise NotImplementedError("No STT backend available. Install faster-whisper or whisper-cli")
    
    def transcribe(self, audio_path: str) -> str:
        """Transcribe audio file to text."""
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        if self.backend == "faster-whisper":
            segments, _ = self._model.transcribe(str(audio_path))
            return " ".join([s.text for s in segments])
        
        elif self.backend == "whisper-cli":
            # Convert to WAV if needed
            wav_path = self._convert_to_wav(audio_path)
            
            # Find model
            model_path = None
            for check in [
                Path.home() / ".voicepipe" / "models" / f"ggml-{self.model}.en.bin",
                Path.home() / ".voicepipe" / "models" / f"ggml-tiny.en.bin",
                Path.home() / "whisper.cpp" / "models" / f"ggml-{self.model}.en.bin",
            ]:
                if check.exists():
                    model_path = check
                    break
            
            if not model_path:
                raise FileNotFoundError(f"Model not found. Run: voicepipe install")
            
            result = subprocess.run(
                [str(self._whisper_path), "-m", str(model_path), "-f", str(wav_path),
                 "-np", "-otxt", "--no-timestamps"],
                capture_output=True, text=True, timeout=120,
            )
            
            # Cleanup temp file
            if wav_path != audio_path:
                wav_path.unlink(missing_ok=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"STT failed: {result.stderr}")
            
            return result.stdout.strip()
        
        elif self.backend == "api":
            raise NotImplementedError("API backend not yet configured")
        
        raise RuntimeError(f"Unknown backend: {self.backend}")
    
    def _convert_to_wav(self, audio_path: Path) -> Path:
        """Convert audio to WAV format."""
        if audio_path.suffix.lower() == ".wav":
            return audio_path
        
        wav_path = audio_path.with_suffix(".wav")
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(audio_path), "-ar", "16000", "-ac", "1", str(wav_path)],
            capture_output=True, timeout=30,
        )
        return wav_path
    
    def transcribe_bytes(self, audio_data: bytes) -> str:
        """Transcribe raw audio bytes."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name
        
        try:
            return self.transcribe(temp_path)
        finally:
            os.unlink(temp_path)