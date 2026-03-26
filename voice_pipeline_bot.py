#!/usr/bin/env python3
"""
Voice Pipeline - Telegram Bot Integration

Watches for voice notes from Telegram → STT → Process → TTS → Reply
"""
import os
import sys
import subprocess
from pathlib import Path

# Watch directory
MEDIA_DIR = Path("/root/.openclaw/media/inbound")
CACHE_DIR = Path("/root/.voicepipe")

def process_voice_note(file_path: str) -> str:
    """Convert voice note to text."""
    # Convert ogg to wav first (Telegram sends ogg)
    wav_path = file_path.replace(".ogg", "_temp.wav")
    
    # FFmpeg convert
    result = subprocess.run([
        "ffmpeg", "-y", "-i", file_path,
        "-ar", "16000", "-ac", "1", wav_path
    ], capture_output=True)
    
    if result.returncode != 0:
        return f"Error converting: {result.stderr.decode()}"
    
    # Run STT
    whisper_path = str(CACHE_DIR / "whisper.cpp/build/bin/whisper-cli")
    model_path = str(CACHE_DIR / "models/ggml-tiny.en.bin")
    
    result = subprocess.run([
        whisper_path, "-m", model_path, "-f", wav_path,
        "-np", "-otxt", "--no-timestamps"
    ], capture_output=True, text=True)
    
    # Cleanup
    if os.path.exists(wav_path):
        os.unlink(wav_path)
    
    if result.returncode == 0:
        return result.stdout.strip()
    else:
        return f"STT Error: {result.stderr}"

def generate_response(text: str) -> str:
    """Simple response generation (placeholder - integrate your LLM here)."""
    text_lower = text.lower()
    
    responses = {
        "hello": "Hello! How can I help you?",
        "hi": "Hi there! What can I do for you?",
        "time": f"The time is {subprocess.run(['date', '+%I:%M %p'], capture_output=True, text=True).stdout.strip()}.",
        "date": f"Today's date is {subprocess.run(['date', '+%B %d, %Y'], capture_output=True, text=True).stdout.strip()}.",
    }
    
    for key, response in responses.items():
        if key in text_lower:
            return response
    
    return f"You said: {text}. I'm a simple response. Add your LLM integration!"

def text_to_speech(text: str) -> bytes:
    """Convert text to speech audio."""
    # Use edge-tts (or any available)
    import tempfile
    import asyncio
    
    async def generate():
        import edge_tts
        communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            mp3_path = f.name
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                with open(mp3_path, "ab") as f:
                    f.write(chunk["data"])
        return mp3_path
    
    try:
        mp3_path = asyncio.run(generate())
        
        # Convert to raw audio
        wav_path = mp3_path.replace(".mp3", ".wav")
        subprocess.run([
            "ffmpeg", "-y", "-i", mp3_path,
            "-ar", "16000", "-ac", "1", wav_path
        ], capture_output=True)
        
        with open(wav_path, "rb") as f:
            audio = f.read()
        
        # Cleanup
        os.unlink(mp3_path)
        os.unlink(wav_path)
        
        return audio
    except Exception as e:
        print(f"TTS Error: {e}")
        return b""

def main():
    """Watch for new voice notes and process them."""
    import time
    
    print("🎤 Voice Pipeline Active")
    print("Watching for voice notes from Telegram...")
    
    # Track processed files
    processed = set()
    
    # Get existing files
    for f in MEDIA_DIR.glob("*.ogg"):
        processed.add(f.name)
    
    while True:
        try:
            # Check for new files
            for f in MEDIA_DIR.glob("*.ogg"):
                if f.name not in processed:
                    print(f"\n📥 New voice note: {f.name}")
                    processed.add(f.name)
                    
                    # Process
                    text = process_voice_note(str(f))
                    print(f"📝 Transcribed: {text}")
                    
                    response = generate_response(text)
                    print(f"🤖 Response: {response}")
                    
                    # TTS (optional - just show for now)
                    audio = text_to_speech(response)
                    print(f"🔊 TTS generated: {len(audio)} bytes")
            
            time.sleep(2)
        except KeyboardInterrupt:
            print("\nStopped.")
            break

if __name__ == "__main__":
    main()