"""VoicePipe system dependency installer.

Handles: ffmpeg, espeak-ng, faster-whisper model download.
Does NOT need whisper-cli anymore — faster-whisper handles everything.
"""

import os
import sys
import shutil
import platform
import urllib.request
import urllib.error
import tarfile
import zipfile
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="[voicepipe] %(message)s")
log = logging.getLogger("voicepipe.installer")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SYSTEM = platform.system().lower()
IS_LINUX = SYSTEM == "linux"
IS_MACOS = SYSTEM == "darwin"
IS_WINDOWS = SYSTEM == "windows"
IS_WSL = "microsoft" in platform.release().lower() if IS_LINUX else False

CACHE_DIR = Path.home() / ".voicepipe"
MODELS_DIR = CACHE_DIR / "models"
FFMPEG_NAMES = ["ffmpeg", "ffmpeg.exe"] if IS_WINDOWS else ["ffmpeg"]
ESPEAK_NAMES = ["espeak-ng"] if not IS_WINDOWS else ["espeaktts.exe", "espeak.exe"]
WHISPER_MODEL_URL = "https://huggingface.co/datasets/ggerganov/whisper.cpp/resolve/main"

# faster-whisper model sizes
MODEL_SIZES = {
    "tiny":   {"file": "ggml-tiny.bin",       "size": "74 MB",   "params": "~39 M"},
    "base":   {"file": "ggml-base.bin",       "size": "140 MB",  "params": "~74 M"},
    "small":  {"file": "ggml-small.bin",      "size": "465 MB",  "params": "~244 M"},
    "medium": {"file": "ggml-medium.bin",     "size": "1.5 GB",  "params": "~769 M"},
    "large":  {"file": "ggml-large-v3.bin",   "size": "2.9 GB",  "params": "~1550 M"},
}

# ---------------------------------------------------------------------------
# Helper: shell commands
# ---------------------------------------------------------------------------
def run(cmd: list[str], check: bool = True, capture: bool = True) -> subprocess.CompletedProcess | None:
    """Run a command, log it, and optionally return its output."""
    log.info(f"  Running: {' '.join(str(c) for c in cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=capture,
            text=True,
        )
        if result.returncode != 0:
            log.error(f"  Command failed (exit {result.returncode}):")
            for line in (result.stderr or result.stdout or "").strip().splitlines()[:10]:
                log.error(f"    {line}")
            if check:
                raise RuntimeError(f"Command failed: {' '.join(str(c) for c in cmd)}")
            return result
        else:
            for line in (result.stdout or "").strip().splitlines()[:5]:
                log.info(f"  → {line}")
            return result
    except FileNotFoundError:
        log.error(f"  Command not found: {cmd[0]}")
        raise


def find_executable(names: list[str]) -> str | None:
    """Find the first available executable from a list of names."""
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    return None


# ---------------------------------------------------------------------------
# System dependency checks
# ---------------------------------------------------------------------------
def check_ffmpeg() -> bool:
    """Check if ffmpeg is available."""
    return find_executable(FFMPEG_NAMES) is not None


def check_espeak() -> bool:
    """Check if espeak-ng is available."""
    return find_executable(ESPEAK_NAMES) is not None


def check_whisper_model(model: str = "base") -> bool:
    """Check if a faster-whisper-compatible GGML model file is cached."""
    if model not in MODEL_SIZES:
        log.warning(f"Unknown model size '{model}'. Available: {list(MODEL_SIZES.keys())}")
        model = "base"
    model_file = MODELS_DIR / MODEL_SIZES[model]["file"]
    return model_file.exists()


def check_faster_whisper() -> bool:
    """Check if faster-whisper Python package is installed."""
    try:
        import faster_whisper
        return True
    except ImportError:
        return False


def check_all() -> dict:
    """Return status of all system dependencies."""
    return {
        "ffmpeg": check_ffmpeg(),
        "espeak_ng": check_espeak(),
        "faster_whisper": check_faster_whisper(),
        "model_base": check_whisper_model("base"),
        "model_tiny": check_whisper_model("tiny"),
    }


# ---------------------------------------------------------------------------
# Install helpers
# ---------------------------------------------------------------------------
def install_ffmpeg() -> bool:
    """Install ffmpeg based on OS."""
    log.info("Installing ffmpeg...")
    if IS_LINUX:
        pkg_managers = [
            (["sudo", "apt-get", "install", "-y", "ffmpeg"], "apt"),
            (["sudo", "dnf", "install", "-y", "ffmpeg"], "dnf/fedora"),
            (["sudo", "pacman", "-S", "--noconfirm", "ffmpeg"], "arch"),
            (["sudo", "apk", "add", "ffmpeg"], "alpine"),
        ]
        for cmd, name in pkg_managers:
            try:
                result = run(cmd, check=False)
                if result and result.returncode == 0:
                    log.info(f"  ffmpeg installed via {name}")
                    return True
            except Exception:
                continue
        log.warning("  Could not auto-install ffmpeg. Please install manually:")
        log.warning("    Ubuntu/Debian: sudo apt install ffmpeg")
        log.warning("    Fedora: sudo dnf install ffmpeg")
        log.warning("    macOS: brew install ffmpeg")
        return False

    elif IS_MACOS:
        try:
            run(["brew", "install", "ffmpeg"], check=True)
            return True
        except Exception:
            log.warning("  Could not install via brew. Try: brew install ffmpeg")
            return False

    elif IS_WINDOWS:
        log.warning("  On Windows, install ffmpeg via:")
        log.warning("    winget install ffmpeg  OR  https://ffmpeg.org/download.html")
        return False

    return False


def install_espeak() -> bool:
    """Install espeak-ng based on OS."""
    if IS_WINDOWS:
        log.info("  espeak-ng not needed on Windows (pyttsx3 is used instead)")
        return True

    log.info("Installing espeak-ng...")
    if IS_LINUX:
        pkg_managers = [
            (["sudo", "apt-get", "install", "-y", "espeak-ng"], "apt"),
            (["sudo", "dnf", "install", "-y", "espeak-ng"], "dnf/fedora"),
            (["sudo", "pacman", "-S", "--noconfirm", "espeak-ng"], "arch"),
        ]
        for cmd, name in pkg_managers:
            try:
                result = run(cmd, check=False)
                if result and result.returncode == 0:
                    log.info(f"  espeak-ng installed via {name}")
                    return True
            except Exception:
                continue
        log.warning("  Could not auto-install espeak-ng.")
        log.warning("    Ubuntu/Debian: sudo apt install espeak-ng")
        return False

    elif IS_MACOS:
        try:
            run(["brew", "install", "espeak-ng"], check=True)
            return True
        except Exception:
            log.warning("  Could not install espeak-ng via brew. Try: brew install espeak-ng")
            return False

    return False


def install_faster_whisper() -> bool:
    """Install faster-whisper Python package."""
    log.info("Installing faster-whisper (STT engine)...")
    try:
        # Try uv first, fall back to pip
        result = run(["uv", "pip", "install", "faster-whisper"], check=False)
        if not result or result.returncode != 0:
            # Fall back to pip with break-system-packages
            for cmd in [
                [sys.executable, "-m", "pip", "install", "faster-whisper"],
                [sys.executable, "-m", "pip", "install", "--break-system-packages", "faster-whisper"],
            ]:
                result = run(cmd, check=False)
                if result and result.returncode == 0:
                    break
        # Verify it actually imported
        import faster_whisper
        log.info("  faster-whisper installed successfully")
        return True
    except Exception as e:
        log.error(f"  Failed to install faster-whisper: {e}")
        return False


def download_model(model: str = "base") -> bool:
    """Download a faster-whisper GGML model from Hugging Face."""
    if model not in MODEL_SIZES:
        model = "base"

    info = MODEL_SIZES[model]
    filename = info["file"]
    dest = MODELS_DIR / filename
    size_str = info["size"]

    if dest.exists():
        log.info(f"  Model already cached: {dest}")
        return True

    log.info(f"Downloading '{model}' model (~{size_str})...")
    log.info(f"  URL: {WHISPER_MODEL_URL}/{filename}")
    log.info(f"  Destination: {dest}")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    url = f"{WHISPER_MODEL_URL}/{filename}"
    try:
        # Use wget/curl with progress (faster and shows progress)
        if find_executable(["wget"]):
            run(["wget", "-O", str(dest), url], check=True)
        elif find_executable(["curl"]):
            run(["curl", "-L", "-o", str(dest), url], check=True)
        else:
            # Fall back to Python urllib
            def _progress(count, block_size, total_size):
                pct = int(count * block_size * 100 / total_size) if total_size > 0 else 0
                if count % 500 == 0:
                    log.info(f"  Downloaded: {pct}%")

            urllib.request.urlretrieve(url, str(dest), _progress)

    except Exception as e:
        log.error(f"  Download failed: {e}")
        if dest.exists():
            log.info(f"  Removing incomplete file...")
            dest.unlink(missing_ok=True)
        return False

    if dest.exists() and dest.stat().st_size > 1024 * 1024:
        log.info(f"  Download complete: {dest.stat().st_size / 1024 / 1024:.1f} MB")
        return True
    else:
        log.error("  Downloaded file seems invalid (too small)")
        return False


# ---------------------------------------------------------------------------
# Top-level installer
# ---------------------------------------------------------------------------
def install_all(
    model: str = "base",
    skip_model: bool = False,
    skip_system: bool = False,
) -> dict:
    """Install everything needed for VoicePipe to work.

    Args:
        model: Which whisper model to download ("tiny", "base", "small", etc.)
        skip_model: Skip downloading the STT model
        skip_system: Skip installing system packages (ffmpeg, espeak-ng)

    Returns:
        dict with "ok" (bool), "message" (str), and "details" (dict)
    """
    log.info("=" * 60)
    log.info("VoicePipe Installer — setting up your voice stack")
    log.info("=" * 60)

    results = {
        "ffmpeg": False,
        "espeak": False,
        "faster_whisper": False,
        "model": False,
    }

    # 1. System dependencies
    if not skip_system:
        if check_ffmpeg():
            log.info("✓ ffmpeg — already installed")
            results["ffmpeg"] = True
        else:
            results["ffmpeg"] = install_ffmpeg()

        if IS_LINUX or IS_MACOS:
            if check_espeak():
                log.info("✓ espeak-ng — already installed")
                results["espeak"] = True
            else:
                results["espeak"] = install_espeak()
        else:
            results["espeak"] = True  # Not needed on Windows

    # 2. Python packages
    if check_faster_whisper():
        log.info("✓ faster-whisper — already installed")
        results["faster_whisper"] = True
    else:
        results["faster_whisper"] = install_faster_whisper()

    # 3. STT Model
    if skip_model:
        log.info("Skipping model download (--skip-model)")
    elif check_whisper_model(model):
        log.info(f"✓ Model '{model}' — already cached")
        results["model"] = True
    else:
        results["model"] = download_model(model)
        if not results["model"]:
            log.warning(
                f"\n  ⚠ Model download failed. You can retry with:"
                f"\n    voicepipe install --model {model}"
            )

    # Summary
    log.info("=" * 60)
    log.info("Installation Summary:")
    all_ok = all(results.values())
    for key, val in results.items():
        status = "✓" if val else "✗"
        log.info(f"  {status} {key}: {'ok' if val else 'FAILED'}")

    if all_ok:
        msg = "VoicePipe is ready! Run: voicepipe --help"
    else:
        failed = [k for k, v in results.items() if not v]
        msg = f"Partially installed. Failed: {', '.join(failed)}"

    log.info(f"\n{msg}\n")
    return {"ok": all_ok, "message": msg, "details": results}
