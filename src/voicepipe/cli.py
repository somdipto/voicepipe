"""
VoicePipe CLI

Usage:
    voicepipe install    - Install all dependencies
    voicepipe status    - Check installation status
    voicepipe agent     - Start voice agent
    voicepipe tts "text" - Text to speech
    voicepipe stt file  - Speech to text
"""
import argparse
import sys
from voicepipe import VoicePipeline
from voicepipe.installer import AutoInstaller
from voicepipe.agent import VoiceAgent


def main():
    parser = argparse.ArgumentParser(
        description="VoicePipe - One-command voice for any app"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install all dependencies")
    install_parser.add_argument("--force", action="store_true", help="Force reinstall")
    
    # Status command
    subparsers.add_parser("status", help="Check installation status")
    
    # Agent command
    subparsers.add_parser("agent", help="Start voice agent")
    
    # TTS command
    tts_parser = subparsers.add_parser("tts", help="Text to speech")
    tts_parser.add_argument("text", help="Text to speak")
    tts_parser.add_argument("-o", "--output", default="output.wav", help="Output file")
    tts_parser.add_argument("-v", "--voice", default="en", help="Voice")
    
    # STT command
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
        print(f"Converting to speech: {args.text}")
        
        try:
            voice = VoicePipeline()
            output = voice.text_to_speech_file(args.text, args.output)
            print(f"✅ Saved to: {output}")
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
                with open(args.output, "w") as f:
                    f.write(text)
                print(f"✅ Saved to: {args.output}")
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
