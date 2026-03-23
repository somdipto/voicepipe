"""
VoicePipe CLI - Fixed version
"""
import argparse
import sys
import wave
from pathlib import Path
from voicepipe import VoicePipeline
from voicepipe.installer import AutoInstaller
from voicepipe.agent import VoiceAgent


def main():
    parser = argparse.ArgumentParser(description="VoicePipe - One-command voice for any app")
    subparsers = parser.add_subparsers(dest="command")
    
    install_parser = subparsers.add_parser("install", help="Install all dependencies")
    install_parser.add_argument("--force", action="store_true", help="Force reinstall")
    
    subparsers.add_parser("status", help="Check installation status")
    subparsers.add_parser("agent", help="Start voice agent")
    
    tts_parser = subparsers.add_parser("tts", help="Text to speech")
    tts_parser.add_argument("text", nargs="+", help="Text to speak")
    tts_parser.add_argument("-o", "--output", default="output.wav", help="Output file")
    tts_parser.add_argument("-v", "--voice", default="en", help="Voice")
    
    stt_parser = subparsers.add_parser("stt", help="Speech to text")
    stt_parser.add_argument("file", help="Audio file")
    stt_parser.add_argument("-o", "--output", help="Output file")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "install":
        print("Installing all dependencies...")
        installer = AutoInstaller()
        results = installer.install_all(force=args.force)
        
        for key, result in results.items():
            if isinstance(result, dict):
                status = result.get("status", "unknown")
            else:
                status = str(result)
            print(f"  {key}: {status}")
        
        if results.get("success"):
            print("\n✅ Installation complete!")
        else:
            print("\n⚠️ Some installations failed. Check status with: voicepipe status")
    
    elif args.command == "status":
        print("Checking status...")
        installer = AutoInstaller()
        status = installer.check_status()
        
        print(f"OS: {status.get('os', 'unknown')}")
        print(f"FFmpeg: {'✅' if status.get('ffmpeg') else '❌'}")
        print(f"Whisper: {'✅' if status.get('whisper') else '❌'}")
        print(f"Model: {'✅' if status.get('model') else '❌'}")
        print(f"Cache: {status.get('cache_dir', 'unknown')}")
    
    elif args.command == "agent":
        print("Starting VoiceAgent...")
        print("Press Ctrl+C to stop")
        
        agent = VoiceAgent()
        try:
            import asyncio
            asyncio.run(agent.run())
        except KeyboardInterrupt:
            print("\nStopped.")
    
    elif args.command == "tts":
        text = " ".join(args.text)
        print(f"Converting to speech: {text}")
        
        try:
            voice = VoicePipeline()
            audio = voice.text_to_speech(text)
            
            # Fix: Proper WAV writing
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if audio has WAV header
            if audio[:4] == b'RIFF':
                # Has WAV header, save directly
                with open(output_path, 'wb') as f:
                    f.write(audio)
            else:
                # Raw PCM, create WAV
                # Determine sample rate from backend (gTTS = 24kHz)
                with wave.open(str(output_path), 'wb') as f:
                    f.setnchannels(1)  # Mono
                    f.setsampwidth(2)  # 16-bit
                    f.setframerate(24000)  # 24kHz
                    f.writeframes(audio)
            
            print(f"✅ Saved to: {output_path}")
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    
    elif args.command == "stt":
        print(f"Transcribing: {args.file}")
        
        try:
            voice = VoicePipeline()
            text = voice.speech_to_text(args.file)
            print(f"You said: {text}")
            
            if args.output:
                Path(args.output).write_text(text)
                print(f"✅ Saved to: {args.output}")
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
