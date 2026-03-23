"""
VoicePipe CLI
"""
import argparse
import sys
from pathlib import Path
from voicepipe import VoicePipeline


def main():
    parser = argparse.ArgumentParser(
        description="VoicePipe - One-command STT + TTS"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Transcribe command
    transcribe_parser = subparsers.add_parser("transcribe", help="Convert speech to text")
    transcribe_parser.add_argument("audio", help="Audio file path")
    transcribe_parser.add_argument("-o", "--output", help="Output file for text")
    transcribe_parser.add_argument("-m", "--model", default="tiny", choices=["tiny", "base", "small"])
    
    # Speak command
    speak_parser = subparsers.add_parser("speak", help="Convert text to speech")
    speak_parser.add_argument("text", help="Text to speak")
    speak_parser.add_argument("-o", "--output", default="output.wav", help="Output audio file")
    speak_parser.add_argument("-v", "--voice", default="Bella", help="Voice name")
    speak_parser.add_argument("-s", "--speed", type=float, default=1.0, help="Speech speed")
    
    # Voices command
    subparsers.add_parser("voices", help="List available TTS voices")
    
    # Status command
    subparsers.add_parser("status", help="Show voice pipeline status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize voice pipeline
    voice = VoicePipeline()
    
    if args.command == "transcribe":
        try:
            text = voice.speech_to_text(args.audio)
            if args.output:
                Path(args.output).write_text(text)
                print(f"Transcribed text saved to: {args.output}")
            else:
                print(text)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.command == "speak":
        try:
            output_path = voice.text_to_speech_file(args.text, args.output)
            print(f"Audio saved to: {output_path}")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.command == "voices":
        voices = voice.list_voices()
        print("Available voices:")
        for v in voices:
            print(f"  - {v}")
    
    elif args.command == "status":
        status = voice.get_status()
        print("VoicePipe Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()