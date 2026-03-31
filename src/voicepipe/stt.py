"""Speech-to-text backends for VoicePipe.

Priority: faster-whisper (offline, fast, CPU) → whisper-cli → api (stub)
"""

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Literal
from abc import ABC, abstractmethod
from dataclasses import dataclass

log = logging.getLogger("voicepipe.stt")

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------
Backend = Literal["faster-whisper", "whisper-cli", "api"]
ModelSize = Literal["tiny", "base", "small", "medium", "large", "turbo"]

@dataclass
class STTResult:
    text: str
    language: str | None = None
    backend: Backend | None = None
    duration: float | None = None

# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------
class BaseSTT(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str | Path, **kwargs) -> STTResult:
        ...

# ---------------------------------------------------------------------------
# faster-whisper (PRIMARY — offline, fast, accurate)
# ---------------------------------------------------------------------------
class FasterWhisperSTT(BaseSTT):
    """Faster-Whisper STT engine.

    Downloads GGML-format Whisper models automatically.
    Works fully offline after model is cached.
    """

    MODELS = {
        "tiny":   {"file": "ggml-tiny.bin",       "hf": "ggerganov/whisper.cpp", "size": "74 MB"},
        "base":   {"file": "ggml-base.bin",       "hf": "ggerganov/whisper.cpp", "size": "140 MB"},
        "small":  {"file": "ggml-small.bin",      "hf": "ggerganov/whisper.cpp", "size": "465 MB"},
        "medium": {"file": "ggml-medium.bin",     "hf": "ggerganov/whisper.cpp", "size": "1.5 GB"},
        "large":  {"file": "ggml-large-v3.bin",   "hf": "ggerganov/whisper.cpp", "size": "2.9 GB"},
        "turbo":  {"file": "ggml-turbo.bin",      "hf": "ggerganov/whisper.cpp", "size": "378 MB"},
    }

    def __init__(
        self,
        model: ModelSize = "base",
        device: str = "auto",  # auto, cpu, cuda, cuda:0
        compute_type: str = "auto",  # auto, int8, float16, float32
        download_root: str | None = None,
    ):
        self.model_name = model
        self.device = device
        self.compute_type = compute_type
        self.download_root = download_root or str(Path.home() / ".cache" / "huggingface" / "hub")

        try:
            import faster_whisper
        except ImportError:
            raise RuntimeError(
                "faster-whisper not installed.\n"
                "  pip install faster-whisper\n"
                "  or: voicepipe install"
            )

        self._model = None

    def _load_model(self):
        """Lazy-load the model (downloads on first use if needed)."""
        if self._model is not None:
            return

        import faster_whisper
        model_info = self.MODELS.get(self.model_name, self.MODELS["base"])

        log.info(f"Loading faster-whisper model '{self.model_name}'...")
        self._model = faster_whisper.load_model(
            self.model_name,
            device=self.device,
            download_root=self.download_root,
        )
        log.info(f"  Model loaded: {self._model}")

    def transcribe(self, audio_path: str | Path, **kwargs) -> STTResult:
        self._load_model()

        import faster_whisper
        audio_path = str(audio_path)

        # Convert to WAV 16kHz mono if needed
        import subprocess
        temp_wav = None
        try:
            # Check if ffmpeg is available
            if subprocess.run(["which", "ffmpeg"], capture_output=True).returncode != 0:
                log.warning("ffmpeg not found — audio may not be in the right format")

            # Convert to WAV 16kHz mono via ffmpeg
            temp_wav = audio_path
            result = subprocess.run(
                [
                    "ffmpeg", "-y", "-i", audio_path,
                    "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
                    "-f", "wav", "-"
                ],
                capture_output=True,
                check=True,
            )
            audio_data = result.stdout
            segments, info = self._model.transcribe(
                audio_data,
                beam_size=kwargs.get("beam_size", 5),
                language=kwargs.get("language", None),
                task=kwargs.get("task", "transcribe"),
            )

            text_parts = []
            for seg in segments:
                text_parts.append(seg.text.strip())

            full_text = " ".join(text_parts).strip()
            return STTResult(
                text=full_text,
                language=info.language,
                backend="faster-whisper",
                duration=info.duration,
            )
        except subprocess.CalledProcessError as e:
            log.error(f"ffmpeg conversion failed: {e.stderr}")
            # Try direct transcription as fallback
            segments, info = self._model.transcribe(audio_path, **kwargs)
            text_parts = [s.text.strip() for s in segments]
            return STTResult(
                text=" ".join(text_parts).strip(),
                language=info.language,
                backend="faster-whisper",
            )


# ---------------------------------------------------------------------------
# whisper-cli (DEPRECATED — kept for compatibility)
# ---------------------------------------------------------------------------
class WhisperCLISTT(BaseSTT):
    """Whisper CLI (whisper.cpp) STT engine.

    Deprecated — faster-whisper is faster and easier to install.
    This backend is kept for users who explicitly want it.
    """

    BINARY_NAMES = ["whisper-cli", "main", "whisper"]

    def __init__(self, model: ModelSize = "base", model_path: str | None = None):
        self.model_name = model
        self.binary = self._find_binary()
        self.model_path = model_path or self._default_model_path()

    def _find_binary(self) -> Path:
        for name in self.BINARY_NAMES:
            path = Path(shutil.which(name) or "")
            if path.exists():
                return path
        raise RuntimeError(
            f"whisper-cli binary not found.\n"
            f"  Searched: {', '.join(self.BINARY_NAMES)}\n"
            f"  Install with: voicepipe install --backend whisper-cli\n"
            f"  Or use faster-whisper (recommended): voicepipe install --backend faster-whisper"
        )

    def _default_model_path(self) -> Path:
        cache = Path.home() / ".voicepipe" / "models"
        return cache

    def transcribe(self, audio_path: str | Path, **kwargs) -> STTResult:
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        model = self.model_name
        model_file = self.model_path / f"ggml-{model}.bin"

        if not model_file.exists():
            raise FileNotFoundError(
                f"Model file not found: {model_file}\n"
                f"  Download with: voicepipe install --model {model}"
            )

        # Convert to WAV 16kHz mono
        wav_path = audio_path.with_suffix(".wav")
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(audio_path),
                 "-ar", "16000", "-ac", "1", "-f", "wav", str(wav_path)],
                check=True, capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffmpeg conversion failed: {e.stderr}")

        cmd = [
            str(self.binary),
            "-m", str(model_file),
            "-f", str(wav_path),
            "--language", kwargs.get("language", "en"),
            "--no-timestamps",
            "--print-special",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        text = result.stdout.strip()

        return STTResult(text=text, backend="whisper-cli")


# ---------------------------------------------------------------------------
# API STT (stub)
# ---------------------------------------------------------------------------
class APISTT(BaseSTT):
    """API-based STT (OpenAI Whisper API or similar)."""

    def __init__(self, api_key: str | None = None, model: str = "whisper-1"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model

    def transcribe(self, audio_path: str | Path, **kwargs) -> STTResult:
        raise NotImplementedError("API STT is not yet implemented")


# ---------------------------------------------------------------------------
# Factory + detection
# ---------------------------------------------------------------------------
def detect_backends() -> dict[str, bool]:
    """Detect which STT backends are available."""
    backends = {}
    import shutil

    for name in WhisperCLISTT.BINARY_NAMES:
        backends["whisper-cli"] = shutil.which(name) is not None
        if backends["whisper-cli"]:
            break

    try:
        import faster_whisper
        backends["faster-whisper"] = True
    except ImportError:
        backends["faster-whisper"] = False

    backends["api"] = bool(os.environ.get("OPENAI_API_KEY", ""))

    return backends


def detect_stt() -> str:
    """Return the best available STT backend."""
    backends = detect_backends()
    if backends.get("faster-whisper"):
        return "faster-whisper"
    if backends.get("whisper-cli"):
        return "whisper-cli"
    if backends.get("api"):
        return "api"
    return "none"


# ---------------------------------------------------------------------------
# Main STT class
# ---------------------------------------------------------------------------
class STT:
    """VoicePipe STT — unified interface across backends.

    Auto-detects the best available backend. Use `backend=` to override.

    Examples:
        stt = STT()  # auto-detect
        stt = STT(backend="faster-whisper", model="base")
        result = stt.transcribe("recording.ogg")
        print(result.text)
    """

    def __init__(
        self,
        backend: Backend | None = None,
        model: ModelSize = "base",
        **kwargs,
    ):
        self.backend_name = backend or detect_stt()
        self.model = model
        self.kwargs = kwargs
        self._engine: BaseSTT | None = None

    def _get_engine(self) -> BaseSTT:
        if self._engine is not None:
            return self._engine

        if self.backend_name == "faster-whisper":
            self._engine = FasterWhisperSTT(model=self.model, **self.kwargs)
        elif self.backend_name == "whisper-cli":
            self._engine = WhisperCLISTT(model=self.model, **self.kwargs)
        elif self.backend_name == "api":
            self._engine = APISTT(**self.kwargs)
        else:
            available = detect_backends()
            raise RuntimeError(
                f"No STT backend available. Install options:\n"
                f"  pip install faster-whisper  # recommended (offline, fast)\n"
                f"  Available backends: {available}"
            )

        return self._engine

    def transcribe(self, audio_path: str | Path, **kwargs) -> STTResult:
        """Transcribe an audio file to text.

        Args:
            audio_path: Path to audio file (any format ffmpeg supports)

        Returns:
            STTResult with .text, .language, .backend, .duration
        """
        return self._get_engine().transcribe(audio_path, **kwargs)

    def __call__(self, audio_path: str | Path, **kwargs) -> STTResult:
        """Convenience: stt("audio.ogg") == stt.transcribe("audio.ogg")"""
        return self.transcribe(audio_path, **kwargs)
