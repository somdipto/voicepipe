"""VoicePipe CLI — speech-to-text and text-to-speech from the terminal.

Usage:
    voicepipe --help
    voicepipe --status
    voicepipe --version
    voicepipe install
    voicepipe listen
    voicepipe speak "Hello world"
    voicepipe transcribe audio.ogg
    voicepipe speak "Hi" --voice en-US-AriaNeural --output hello.mp3
"""

import os
import sys
import typer
import shutil
from pathlib import Path
from typing import Optional

# Add src to path for local dev
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from voicepipe import __version__
from voicepipe.stt import STT, detect_stt, detect_backends, FasterWhisperSTT
from voicepipe.tts import TTS
from voicepipe.installer import install_all, check_all

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = typer.Typer(
    add_completion=False,
    help=__doc__,
    no_args_is_help=False,
)

# ---------------------------------------------------------------------------
# Install subcommand
# ---------------------------------------------------------------------------
install_app = typer.Typer(help="Install VoicePipe dependencies.")
app.add_typer(install_app, name="install")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def print_status():
    """Print system dependency status."""
    print(f"\n{'─' * 50}")
    print(f"  VoicePipe v{__version__} — Status")
    print(f"{'─' * 50}")

    status = check_all()

    checks = [
        ("ffmpeg",           "Audio conversion (required)"),
        ("faster_whisper",   "STT engine (offline, fast)"),
        ("espeak_ng",        "Offline TTS engine"),
        ("model_tiny",       "Tiny model (~74 MB)"),
        ("model_base",       "Base model (~140 MB)"),
    ]

    all_ok = True
    for key, label in checks:
        val = status.get(key, False)
        icon = "✓" if val else "✗"
        print(f"  {icon} {label}: {'ok' if val else 'MISSING'}")
        if not val:
            all_ok = False

    stt_backend = detect_stt()
    print(f"\n  STT backend: {stt_backend}")

    if stt_backend == "none":
        print(f"\n  ⚠ No STT engine available.")
        print(f"    Run: voicepipe install")
        print(f"    Or:  pip install faster-whisper")
    else:
        print(f"\n  ✓ Ready to transcribe!")
        print(f"    voicepipe transcribe audio.ogg")
        print(f"    voicepipe listen")

    print(f"{'─' * 50}\n")


# ---------------------------------------------------------------------------
# Global flags (these run BEFORE any subcommand)
# ---------------------------------------------------------------------------
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show version and exit."),
    status: bool = typer.Option(False, "--status", help="Check system dependencies."),
    install: bool = typer.Option(False, "--install", hidden=True),
):
    """VoicePipe — offline-first speech for agents and humans.

    Run `voicepipe --status` to check if everything is installed.
    Run `voicepipe install` to install dependencies.
    Run `voicepipe --help` for full command reference.
    """
    # --version flag (works without running install)
    if version:
        print(f"VoicePipe v{__version__}")
        raise typer.Exit(0)

    # --status flag (works without running install)
    if status:
        print_status()
        raise typer.Exit(0)

    # --install flag (legacy, kept for compatibility)
    if install:
        typer.echo("DEPRECATED: Use `voicepipe install` instead of `voicepipe --install`")
        raise typer.Exit(1)

    # No command given — show help
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        typer.echo("\nQuick start:")
        typer.echo("  voicepipe --status          # check what's installed")
        typer.echo("  voicepipe install            # install dependencies")
        typer.echo("  voicepipe transcribe audio.ogg   # STT")
        typer.echo("  voicepipe speak 'Hello'     # TTS")
        raise typer.Exit(0)


# ---------------------------------------------------------------------------
# install subcommand
# ---------------------------------------------------------------------------
@install_app.command()
def default(
    model: str = typer.Option("base", "--model", "-m",
        help="Whisper model size: tiny, base, small, medium, large"),
    skip_model: bool = typer.Option(False, "--skip-model",
        help="Skip downloading the STT model"),
    skip_system: bool = typer.Option(False, "--skip-system",
        help="Skip installing system packages (ffmpeg, espeak-ng)"),
):
    """Install VoicePipe dependencies (ffmpeg, faster-whisper, STT model)."""
    result = install_all(
        model=model,
        skip_model=skip_model,
        skip_system=skip_system,
    )
    if result["ok"]:
        raise typer.Exit(0)
    else:
        typer.secho(f"Installation incomplete: {result['message']}", fg=typer.colors.RED)
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# listen command (mic → STT → print text)
# ---------------------------------------------------------------------------
@app.command()
def listen(
    model: str = typer.Option("base", "--model", "-m",
        help="Whisper model size"),
    backend: str = typer.Option(None, "--backend", "-b",
        help="STT backend: faster-whisper, whisper-cli, api"),
    language: str = typer.Option(None, "--language", "-l",
        help="Language code (auto-detect if not set)"),
    duration: float = typer.Option(5.0, "--duration", "-d",
        help="Recording duration in seconds"),
):
    """Listen from microphone and transcribe in real-time."""
    typer.echo(f"Listening for {duration}s... (Ctrl+C to stop)")

    try:
        import sounddevice as sd
        import numpy as np
    except ImportError:
        typer.secho(
            "sounddevice not installed. Run: pip install sounddevice numpy",
            fg=typer.colors.RED
        )
        raise typer.Exit(1)

    typer.echo("Recording...")
    recording = sd.rec(int(duration * 16000), samplerate=16000, channels=1, dtype='float32')
    sd.wait()
    typer.echo("Transcribing...")

    # Save temp WAV
    import tempfile, soundfile as sf
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, recording, 16000)
        temp_path = f.name

    try:
        stt = STT(backend=backend or detect_stt() or "faster-whisper", model=model)
        result = stt.transcribe(temp_path, language=language)
        typer.secho(f"\n{result.text}\n", fg=typer.colors.GREEN)
    finally:
        Path(temp_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# transcribe command (file → STT → print text)
# ---------------------------------------------------------------------------
@app.command()
def transcribe(
    audio: str = typer.Argument(..., help="Path to audio file (any format ffmpeg supports)"),
    model: str = typer.Option("base", "--model", "-m", help="Whisper model size"),
    backend: str = typer.Option(None, "--backend", "-b",
        help="STT backend: faster-whisper (default), whisper-cli"),
    language: str = typer.Option(None, "--language", "-l",
        help="Language code (auto-detect if not set)"),
    output: str = typer.Option(None, "--output", "-o",
        help="Save transcript to file"),
):
    """Transcribe an audio file to text.

    Examples:
        voicepipe transcribe recording.ogg
        voicepipe transcribe audio.mp3 --model small --language es
        voicepipe transcribe audio.wav -o transcript.txt
    """
    audio_path = Path(audio)
    if not audio_path.exists():
        typer.secho(f"Error: File not found: {audio}", fg=typer.colors.RED)
        raise typer.Exit(1)

    detected = backend or detect_stt()
    if detected == "none":
        typer.secho(
            "No STT engine found. Run: voicepipe install\n"
            "  Or manually: pip install faster-whisper",
            fg=typer.colors.RED
        )
        raise typer.Exit(1)

    typer.echo(f"Transcribing: {audio_path.name}")
    typer.echo(f"  Backend: {detected}, Model: {model}")

    try:
        stt = STT(backend=detected, model=model)
        result = stt.transcribe(audio_path, language=language)
    except Exception as e:
        typer.secho(f"Transcription failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

    if output:
        Path(output).write_text(result.text)
        typer.secho(f"Transcript saved: {output}", fg=typer.colors.GREEN)
    else:
        typer.secho(f"\n{result.text}\n", fg=typer.colors.GREEN)
        if result.language:
            typer.echo(f"  Detected language: {result.language}")


# ---------------------------------------------------------------------------
# speak command (text → TTS → play audio)
# ---------------------------------------------------------------------------
@app.command()
def speak(
    text: str = typer.Argument(..., help="Text to speak"),
    voice: str = typer.Option("en-US-AriaNeural", "--voice", "-v",
        help="edge-tts voice name"),
    output: str = typer.Option(None, "--output", "-o",
        help="Save audio to file instead of playing"),
    backend: str = typer.Option("edge-tts", "--backend", "-b",
        help="TTS backend: edge-tts, gtts, espeak, pyttsx3"),
):
    """Convert text to speech and play or save it.

    Examples:
        voicepipe speak "Hello, this is VoicePipe!"
        voicepipe speak "Hola" --voice es-ES-AlvaroNeural
        voicepipe speak "Hello" --output hello.mp3
    """
    if not output and not sys.stdout.isatty():
        typer.secho("Error: No output file and not a TTY — cannot play audio", fg=typer.colors.RED)
        raise typer.Exit(1)

    try:
        tts = TTS(backend=backend)
        audio_path = tts.speak(text, voice=voice, output=output)
        if output:
            typer.secho(f"Saved: {output}", fg=typer.colors.GREEN)
        else:
            typer.secho(f"Played: {audio_path}", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"TTS failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# version command
# ---------------------------------------------------------------------------
@app.command()
def version():
    """Show version information."""
    print(f"VoicePipe v{__version__}")
    print(f"Python {sys.version.split()[0]}")
    backends = detect_backends()
    print(f"Available STT: {[k for k, v in backends.items() if v]}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app()
