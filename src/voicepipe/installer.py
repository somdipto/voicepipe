"""VoicePipe Installer - One command to install everything."""

import platform
import subprocess
import sys
import logging
from pathlib import Path

logger = logging.getLogger("voicepipe.installer")


def install_all():
    """Install everything system-wide. Run once."""
    os_name = platform.system().lower()
    
    print(f"🔧 Installing VoicePipe dependencies on {os_name}...\n")
    
    # Install system deps
    deps = {
        "linux": ["ffmpeg", "espeak-ng"],
        "darwin": ["ffmpeg", "espeak-ng"],
        "windows": ["ffmpeg"],
    }
    
    packages = deps.get(os_name, [])
    
    for pkg in packages:
        try:
            subprocess.run([pkg, "--version"], capture_output=True, check=True)
            print(f"  ✅ {pkg} already installed")
        except (FileNotFoundError, subprocess.CalledProcessError):
            print(f"  ⚠️ {pkg} not found - installing...")
            _install_system_pkg(pkg, os_name)
    
    # Auto-install Python deps if missing
    python_deps = ["faster-whisper", "sounddevice", "gtts", "edge-tts", "pyttsx3"]
    
    print("\n📦 Installing Python dependencies...")
    for dep in python_deps:
        try:
            __import__(dep.replace("-", "_"))
            print(f"  ✅ {dep} already installed")
        except ImportError:
            print(f"  ⚠️ {dep} not found - installing...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", dep],
                capture_output=True,
            )
            print(f"  ✅ Installed {dep}")
    
    print("\n🎉 VoicePipe ready! Run: voicepipe tts 'hello world'")


def _install_system_pkg(pkg: str, os_name: str):
    """Install system package based on OS."""
    try:
        if os_name == "linux":
            # Try apt-get first
            result = subprocess.run(
                ["sudo", "apt-get", "install", "-y", pkg],
                capture_output=True, timeout=300,
            )
            if result.returncode == 0:
                print(f"  ✅ Installed {pkg}")
                return
            
            # Try dnf
            result = subprocess.run(
                ["sudo", "dnf", "install", "-y", pkg],
                capture_output=True, timeout=300,
            )
            if result.returncode == 0:
                print(f"  ✅ Installed {pkg}")
                return
        
        elif os_name == "darwin":
            result = subprocess.run(
                ["brew", "install", pkg],
                capture_output=True, timeout=300,
            )
            if result.returncode == 0:
                print(f"  ✅ Installed {pkg}")
                return
        
        elif os_name == "windows":
            result = subprocess.run(
                ["choco", "install", pkg, "-y"],
                capture_output=True, timeout=300,
            )
            if result.returncode == 0:
                print(f"  ✅ Installed {pkg}")
                return
        
        print(f"  ❌ Failed to install {pkg}")
    
    except subprocess.TimeoutExpired:
        print(f"  ❌ Timed out installing {pkg}")
    except Exception as e:
        print(f"  ❌ Error installing {pkg}: {e}")


def check_status():
    """Check which backends are available."""
    from voicepipe.stt import detect_stt
    from voicepipe.tts import detect_tts
    
    return {
        "stt": detect_stt(),
        "tts": detect_tts(),
        "ffmpeg": _check_binary("ffmpeg"),
        "espeak-ng": _check_binary("espeak-ng"),
    }


def _check_binary(name: str) -> bool:
    """Check if a binary is installed."""
    try:
        subprocess.run([name, "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False