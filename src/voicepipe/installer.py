"""
Auto-Installer - Fully Fixed Version

Fixed:
- All error handling improved
- Better fallbacks
"""
import subprocess
import platform
import os
import sys
import logging
import shutil
from pathlib import Path

logger = logging.getLogger("voicepipe.installer")

DEFAULT_CACHE_DIR = os.path.expanduser("~/.voicepipe")


class AutoInstaller:
    """Automatic installer for all VoicePipe dependencies."""
    
    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR):
        self.os = platform.system().lower()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def install_all(self, force: bool = False) -> dict:
        """Install all dependencies."""
        results = {}
        
        results["ffmpeg"] = self.install_ffmpeg(force=force)
        results["tts_backends"] = self.install_tts_backends()
        results["whisper"] = self.install_whisper(force=force)
        results["models"] = self.download_models(force=force)
        
        success = True
        for key in ["ffmpeg", "whisper", "models"]:
            if isinstance(results.get(key), dict):
                status = results[key].get("status", "")
                if status not in ["installed", "already", "downloaded"]:
                    success = False
        
        results["success"] = success
        return results
    
    def install_ffmpeg(self, force: bool = False) -> dict:
        """Install FFmpeg."""
        if shutil.which("ffmpeg"):
            return {"status": "already", "message": "FFmpeg already installed"}
        
        logger.info("Installing FFmpeg...")
        
        try:
            if self.os == "darwin":
                result = subprocess.run(
                    ["brew", "install", "ffmpeg"],
                    capture_output=True, text=True, timeout=300,
                )
                if result.returncode == 0:
                    return {"status": "installed", "method": "brew"}
                    
            elif self.os == "linux":
                for cmd in [
                    ["sudo", "apt", "install", "-y", "ffmpeg"],
                    ["sudo", "yum", "install", "-y", "ffmpeg"],
                ]:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    if result.returncode == 0:
                        return {"status": "installed", "method": " ".join(cmd[:3])}
                        
            elif self.os == "windows":
                result = subprocess.run(
                    ["choco", "install", "ffmpeg", "-y"],
                    capture_output=True, text=True, timeout=300,
                )
                if result.returncode == 0:
                    return {"status": "installed", "method": "choco"}
                    
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "message": "Installation timed out"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
        
        return {
            "status": "manual",
            "message": "Please install FFmpeg manually: https://ffmpeg.org/download.html",
        }
    
    def install_tts_backends(self) -> dict:
        """Install TTS backends."""
        backends = {}
        
        for name, package in [("gtts", "gtts"), ("edge_tts", "edge-tts"), ("pyttsx3", "pyttsx3")]:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    capture_output=True, timeout=60,
                )
                backends[name] = "installed" if result.returncode == 0 else "failed"
            except Exception as e:
                backends[name] = f"failed: {e}"
        
        installed = sum(1 for v in backends.values() if v == "installed")
        return {"status": "installed" if installed > 0 else "failed", "backends": backends}
    
    def install_whisper(self, force: bool = False) -> dict:
        """Install whisper.cpp with CMake."""
        whisper_dir = self.cache_dir / "whisper.cpp"
        
        # Check existing - only use cache_dir and PATH
        if not force:
            if whisper_dir.exists():
                check_path = whisper_dir / "build" / "bin" / "whisper-cli"
                if check_path.exists():
                    return {"status": "already", "path": str(check_path)}
            
            # Check PATH
            if shutil.which("whisper-cli"):
                return {"status": "already", "path": shutil.which("whisper-cli")}
        
        logger.info("Installing whisper.cpp...")
        
        try:
            # Clone
            if not whisper_dir.exists():
                result = subprocess.run(
                    ["git", "clone", "--depth", "1", 
                     "https://github.com/ggerganov/whisper.cpp.git",
                     str(whisper_dir)],
                    capture_output=True, text=True, timeout=60,
                )
                if result.returncode != 0:
                    return {"status": "failed", "error": f"git clone failed: {result.stderr}"}
            
            # CMake
            result = subprocess.run(
                ["cmake", "-B", "build", "-DCMAKE_BUILD_TYPE=Release"],
                cwd=str(whisper_dir),
                capture_output=True, text=True, timeout=60,
            )
            
            if result.returncode != 0:
                # Try cmake3
                result = subprocess.run(
                    ["cmake3", "-B", "build", "-DCMAKE_BUILD_TYPE=Release"],
                    cwd=str(whisper_dir),
                    capture_output=True, text=True, timeout=60,
                )
            
            if result.returncode != 0:
                return {"status": "failed", "error": f"cmake failed: {result.stderr}"}
            
            # Build
            result = subprocess.run(
                ["cmake", "--build", "build", "-j", "4", "--config", "Release"],
                cwd=str(whisper_dir),
                capture_output=True, text=True, timeout=300,
            )
            
            whisper_bin = whisper_dir / "build" / "bin" / "whisper-cli"
            if whisper_bin.exists():
                return {"status": "installed", "path": str(whisper_bin)}
            else:
                return {"status": "failed", "error": "Binary not found after build"}
                
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "Installation timed out"}
        except FileNotFoundError as e:
            return {"status": "failed", "error": f"Missing tool: {e}. Install cmake."}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def download_models(self, force: bool = False) -> dict:
        """Download whisper models."""
        models_dir = self.cache_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        
        model_file = "ggml-tiny.en.bin"
        model_path = models_dir / model_file
        
        if not force and model_path.exists() and model_path.stat().st_size > 1000000:
            return {"status": "already", "path": str(model_path)}
        
        logger.info("Downloading whisper model...")
        
        urls = [
            f"https://huggingface.co/danon321/whisper.cpp-models/resolve/main/{model_file}",
            f"https://huggingface.co/ggerganov/whisper.cpp/resolve/main/{model_file}",
        ]
        
        for url in urls:
            try:
                result = subprocess.run(
                    ["curl", "-L", "-o", str(model_path), url],
                    capture_output=True, timeout=300,
                )
                if result.returncode == 0 and model_path.exists() and model_path.stat().st_size > 1000000:
                    return {"status": "downloaded", "path": str(model_path)}
            except Exception as e:
                logger.warning(f"Download failed for {url}: {e}")
        
        return {"status": "failed", "error": "Could not download model"}
    
    def check_status(self) -> dict:
        """Check installation status."""
        whisper_locations = []
        
        # Check cache_dir location
        if self.cache_dir.exists():
            whisper_locations.append(self.cache_dir / "whisper.cpp" / "build" / "bin" / "whisper-cli")
        
        # Also check PATH
        path_whisper = shutil.which("whisper-cli")
        if path_whisper:
            whisper_locations.append(Path(path_whisper))
        
        model_path = self.cache_dir / "models" / "ggml-tiny.en.bin"
        
        return {
            "os": self.os,
            "ffmpeg": bool(shutil.which("ffmpeg")),
            "whisper": any(p.exists() for p in whisper_locations),
            "model": model_path.exists() and model_path.stat().st_size > 1000000,
            "cache_dir": str(self.cache_dir),
        }
    
    def get_whisper_path(self) -> str:
        """Get path to whisper-cli."""
        # Check cache_dir location first
        whisper_path = self.cache_dir / "whisper.cpp" / "build" / "bin" / "whisper-cli"
        if whisper_path.exists():
            return str(whisper_path)
        
        # Check PATH
        path = shutil.which("whisper-cli")
        if path:
            return path
        
        return "whisper-cli"
