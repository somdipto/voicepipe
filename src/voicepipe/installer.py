"""
Auto-Installer - Automatically install all dependencies

One command to install everything:
    from voicepipe.installer import AutoInstaller
    installer = AutoInstaller()
    installer.install_all()
"""
import subprocess
import platform
import os
import sys
import logging
import shutil

logger = logging.getLogger("voicepipe.installer")

DEFAULT_CACHE_DIR = os.path.expanduser("~/.voicepipe")


class AutoInstaller:
    """
    Automatic installer for all VoicePipe dependencies.
    
    Usage:
        from voicepipe.installer import AutoInstaller
        installer = AutoInstaller()
        results = installer.install_all()
    """
    
    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR):
        self.os = platform.system().lower()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_admin(self) -> bool:
        """Check if running with admin privileges."""
        try:
            return os.geteuid() == 0 if hasattr(os, 'geteuid') else False
        except:
            return False
    
    def install_all(self, force: bool = False) -> dict:
        """
        Install all dependencies automatically.
        
        Args:
            force: Reinstall even if already installed
            
        Returns:
            dict: Status of each installation
        """
        results = {}
        
        logger.info("Starting auto-installation...")
        
        # 1. FFmpeg
        results["ffmpeg"] = self.install_ffmpeg(force=force)
        
        # 2. TTS backends
        results["tts_backends"] = self.install_tts_backends()
        
        # 3. STT (whisper)
        results["whisper"] = self.install_whisper(force=force)
        
        # 4. Models
        results["models"] = self.download_models(force=force)
        
        # Summary
        success = all(r.get("status") in ["installed", "already", "ok"] for r in results.values())
        results["success"] = success
        
        logger.info(f"Installation complete. Success: {success}")
        
        return results
    
    def install_ffmpeg(self, force: bool = False) -> dict:
        """Install FFmpeg."""
        # Check if already installed
        if shutil.which("ffmpeg"):
            return {"status": "already", "message": "FFmpeg already installed"}
        
        logger.info("Installing FFmpeg...")
        
        try:
            if self.os == "darwin":
                # macOS
                result = subprocess.run(
                    ["brew", "install", "ffmpeg"],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode == 0:
                    return {"status": "installed", "method": "brew"}
                    
            elif self.os == "linux":
                # Try apt first
                result = subprocess.run(
                    ["sudo", "apt", "install", "-y", "ffmpeg"],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode == 0:
                    return {"status": "installed", "method": "apt"}
                    
                # Try yum
                result = subprocess.run(
                    ["sudo", "yum", "install", "-y", "ffmpeg"],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode == 0:
                    return {"status": "installed", "method": "yum"}
                    
            elif self.os == "windows":
                # Try choco
                result = subprocess.run(
                    ["choco", "install", "ffmpeg", "-y"],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode == 0:
                    return {"status": "installed", "method": "choco"}
                    
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "message": "Installation timed out"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
        
        return {
            "status": "manual", 
            "message": f"Please install FFmpeg manually: https://ffmpeg.org/download.html"
        }
    
    def install_tts_backends(self) -> dict:
        """Install TTS backends."""
        backends = {}
        
        for backend, package in [("gtts", "gtts"), ("edge_tts", "edge-tts"), ("pyttsx3", "pyttsx3")]:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    capture_output=True,
                    timeout=60
                )
                backends[backend] = "installed"
            except:
                backends[backend] = "failed"
        
        return {"status": "installed" if any(b == "installed" for b in backends.values()) else "failed", "backends": backends}
    
    def install_whisper(self, force: bool = False) -> dict:
        """Install whisper.cpp."""
        whisper_dir = self.cache_dir / "whisper.cpp"
        whisper_bin = whisper_dir / "build" / "bin" / "whisper-cli"
        
        # Check if already installed
        if not force and whisper_bin.exists():
            return {"status": "already", "path": str(whisper_bin)}
        
        # Check if binary exists in PATH
        if shutil.which("whisper-cli"):
            return {"status": "already", "path": "system"}
        
        logger.info("Installing whisper.cpp...")
        
        try:
            # Clone
            if not whisper_dir.exists() or force:
                if whisper_dir.exists() and force:
                    shutil.rmtree(whisper_dir)
                    
                result = subprocess.run(
                    ["git", "clone", "--depth", "1", 
                     "https://github.com/ggerganov/whisper.cpp.git",
                     str(whisper_dir)],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode != 0:
                    return {"status": "failed", "error": "git clone failed"}
            
            # Build
            result = subprocess.run(
                ["make", "whisper-cli"],
                cwd=str(whisper_dir),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0 and whisper_bin.exists():
                return {"status": "installed", "path": str(whisper_bin)}
            else:
                return {"status": "failed", "error": "build failed", "output": result.stderr}
                
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "Installation timed out"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def download_models(self, force: bool = False) -> dict:
        """Download whisper models."""
        models_dir = self.cache_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Download tiny model
        model_file = "ggml-tiny.en.bin"
        model_path = models_dir / model_file
        
        if not force and model_path.exists():
            return {"status": "already", "path": str(model_path)}
        
        logger.info("Downloading whisper model...")
        
        # Try multiple sources
        urls = [
            f"https://huggingface.co/danon321/whisper.cpp-models/resolve/main/{model_file}",
            f"https://huggingface.co/ggerganov/whisper.cpp/resolve/main/{model_file}",
        ]
        
        for url in urls:
            try:
                result = subprocess.run(
                    ["curl", "-L", "-o", str(model_path), url],
                    capture_output=True,
                    timeout=300
                )
                
                if result.returncode == 0 and model_path.exists() and model_path.stat().st_size > 1000000:
                    return {"status": "downloaded", "path": str(model_path)}
            except:
                continue
        
        return {"status": "failed", "error": "Could not download model"}
    
    def check_status(self) -> dict:
        """Check installation status."""
        whisper_dir = self.cache_dir / "whisper.cpp"
        
        # Check common locations for whisper
        whisper_locations = [
            whisper_dir / "build" / "bin" / "whisper-cli",
            Path("/root/whisper.cpp/build/bin/whisper-cli"),
            Path("/usr/local/bin/whisper-cli"),
            Path("/usr/bin/whisper-cli"),
        ]
        
        whisper_found = any(p.exists() for p in whisper_locations)
        
        model_path = self.cache_dir / "models" / "ggml-tiny.en.bin"
        
        return {
            "os": self.os,
            "ffmpeg": bool(shutil.which("ffmpeg")),
            "whisper": whisper_found,
            "model": model_path.exists() and model_path.stat().st_size > 1000000,
            "cache_dir": str(self.cache_dir),
        }
    
    def get_whisper_path(self) -> str:
        """Get path to whisper-cli."""
        # Check common locations
        whisper_locations = [
            self.cache_dir / "whisper.cpp" / "build" / "bin" / "whisper-cli",
            Path("/root/whisper.cpp/build/bin/whisper-cli"),
            Path("/usr/local/bin/whisper-cli"),
            Path("/usr/bin/whisper-cli"),
        ]
        
        for p in whisper_locations:
            if p.exists():
                return str(p)
        
        # Check PATH
        path = shutil.which("whisper-cli")
        if path:
            return path
        
        return "whisper-cli"


from pathlib import Path
