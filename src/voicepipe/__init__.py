"""
VoicePipe - Universal Voice Pipeline
One-command STT + TTS for any app

Install: pip install voicepipe
Usage:
    from voicepipe import VoicePipeline
    voice = VoicePipeline()
    text = voice.speech_to_text("audio.wav")
    audio = voice.text_to_speech("Hello!")
"""

__version__ = "0.1.0"
__author__ = "DanLab"

from voicepipe.voice_pipeline import VoicePipeline

__all__ = ["VoicePipeline", "__version__"]