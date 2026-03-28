"""VoicePipe CLI - One command for everything."""

import sys
import argparse
import wave
from pathlib import Path


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="VoicePipe - One-command voice for any app")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # install
    subparsers.add_parser("install", help="Install system dependencies")
    
    # tts
    tts_parser = subparsers.add_parser("tts", help="Text to speech")
    tts_parser.add_argument("text", nargs="+", help="Text to speak")
    tts_parser.add_argument("-o", "--output", default="output.wav", help="Output file")
    tts_parser.add_argument("-b", "--backend", help="TTS backend (edge-tts, gtts, pyttsx3)")
    tts_parser.add_argument("-v", "--voice", default="en", help="Voice")
    
    # stt
    stt_parser = subparsers.add_parser("stt", help="Speech to text")
    stt_parser.add_argument("file", help="Audio file")
    stt_parser.add_argument("-b", "--backend", help="STT backend (faster-whisper, whisper-cli)")
    stt_parser.add_argument("-m", "--model", default="base", help="Model size (tiny, base, small)")
    
    # status
    subparsers.add_parser("status", help="Check available backends")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "install":
        from voicepipe.installer import install_all
        install_all()
    
    elif args.command == "tts":
        text = " ".join(args.text)
        print(f"Converting to speech: {text}")
        
        from voicepipe.tts import TTS
        tts = TTS(backend=args.backend, voice=args.voice)
        audio = tts.speak(text)
        
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(audio)
        
        print(f"✅ Saved to: {output_path}")
    
    elif args.command == "stt":
        print(f"Transcribing: {args.file}")
        
        from voicepipe.stt import STT
        stt = STT(backend=args.backend, model=args.model)
        text = stt.transcribe(args.file)
        
        print(f"You said: {text}")
    
    elif args.command == "status":
        from voicepipe.installer import check_status
        status = check_status()
        
        print("VoicePipe Status:")
        print(f"  STT: {status['stt'] or '❌ Not available'}")
        print(f"  TTS: {status['tts'] or '❌ Not available'}")
        print(f"  ffmpeg: {'✅' if status['ffmpeg'] else '❌'}")
        print(f"  espeak-ng: {'✅' if status['espeak-ng'] else '❌'}")


if __name__ == "__main__":
    main()