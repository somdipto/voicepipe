"""VoicePipe — One-command voice for any app."""

__version__ = "1.1.0"
__author__ = "DanLab"

# Lazy imports — don't crash if optional deps aren't installed
def create_stt(backend=None, model="base", **kwargs):
    """Create STT instance (auto-detects best backend)."""
    from voicepipe.stt import STT
    return STT(backend=backend, model=model, **kwargs)


def create_tts(backend=None, voice="en", **kwargs):
    """Create TTS instance (auto-detects best backend)."""
    from voicepipe.tts import TTS
    return TTS(backend=backend, voice=voice, **kwargs)


def install():
    """Install system dependencies (ffmpeg, espeak-ng)."""
    from voicepipe.installer import install_all
    return install_all()


def status():
    """Check which backends are available."""
    from voicepipe.stt import detect_stt
    from voicepipe.tts import detect_tts
    return {
        "stt": detect_stt(),
        "tts": detect_tts(),
        "version": __version__,
    }