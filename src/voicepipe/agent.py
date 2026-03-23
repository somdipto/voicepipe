"""
VoiceAgent - Fixed version with real microphone input

Issue: listen() returned None always
Fix: Use sounddevice for audio input
"""
import asyncio
import logging
import os
from typing import Optional, Callable, Dict, Any, List
from pathlib import Path

logger = logging.getLogger("voicepipe.agent")

DEFAULT_SYSTEM_PROMPT = """You are VoiceAgent, a helpful voice assistant.

You can help with:
- Answering questions
- Setting reminders
- Sending messages
- Making calls
- And more

Be helpful, concise, and friendly.
"""


class VoiceAgent:
    """
    Voice agent with real microphone input.
    """
    
    def __init__(
        self,
        name: str = "VoiceAgent",
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        voice_pipeline = None,
        continuous: bool = True,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.continuous = continuous
        self.is_running = False
        
        # Initialize voice pipeline
        if voice_pipeline is None:
            from voicepipe import VoicePipeline
            self.voice = VoicePipeline()
        else:
            self.voice = voice_pipeline
        
        # Tools registry
        self.tools: Dict[str, Callable] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register built-in tools."""
        self.tools = {
            "time": self._get_time,
            "date": self._get_date,
            "help": self._help,
        }
    
    async def run(self):
        """Run the agent loop."""
        self.is_running = True
        logger.info(f"{self.name} started. Say 'exit' to quit.")
        
        while self.is_running:
            try:
                # Listen
                audio = await self.listen()
                
                if audio is None:
                    if self.continuous:
                        continue
                    else:
                        break
                
                # Convert to text
                try:
                    text = self.voice.speech_to_text_bytes(audio)
                except Exception as e:
                    logger.error(f"STT failed: {e}")
                    await self.speak("Sorry, I couldn't understand that.")
                    continue
                
                if not text.strip():
                    continue
                
                logger.info(f"You: {text}")
                
                # Check for exit
                if text.lower().strip() in ["exit", "quit", "bye", "goodbye"]:
                    await self.speak("Goodbye!")
                    break
                
                # Process and respond
                response = await self.respond(text)
                
                # Speak response
                await self.speak(response)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                await self.speak("Sorry, I encountered an error.")
        
        self.is_running = False
    
    async def listen(self) -> Optional[bytes]:
        """
        Listen for audio input using microphone.
        
        Returns audio bytes or None if no audio.
        """
        # Try to use sounddevice for microphone input
        try:
            import sounddevice as sd
            import numpy as np
            
            logger.info("Listening... (press Ctrl+C to stop)")
            
            # Record audio
            audio_data = sd.rec(
                int(5 * 16000),  # 5 seconds max, 16kHz
                samplerate=16000,
                channels=1,
                dtype='int16'
            )
            sd.wait()
            
            # Convert to bytes
            audio_bytes = audio_data.tobytes()
            
            if len(audio_bytes) > 1000:  # Only return if we got some audio
                return audio_bytes
            return None
            
        except ImportError:
            # sounddevice not available
            logger.warning("sounddevice not installed. Install with: pip install sounddevice")
            return None
        except Exception as e:
            logger.error(f"Microphone error: {e}")
            return None
    
    async def speak(self, text: str):
        """Speak the response."""
        try:
            audio = self.voice.text_to_speech(text)
            
            # Try to play audio
            try:
                import sounddevice as sd
                import numpy as np
                
                # Convert bytes to numpy
                audio_np = np.frombuffer(audio, dtype=np.int16)
                sd.play(audio_np, 24000)
                sd.wait()
            except ImportError:
                pass
            
            logger.info(f"{self.name}: {text}")
        except Exception as e:
            logger.error(f"TTS failed: {e}")
    
    async def respond(self, text: str) -> str:
        """Process input and generate response."""
        text_lower = text.lower().strip()
        
        # Check tools
        for tool_name, tool_func in self.tools.items():
            if tool_name in text_lower:
                try:
                    result = tool_func(text)
                    if asyncio.iscoroutine(result):
                        result = await result
                    return result
                except Exception as e:
                    return f"Error: {e}"
        
        # Default responses
        responses = {
            "hello": "Hello! How can I help you?",
            "hi": "Hi there! What can I do for you?",
            "how are you": "I'm doing great, thanks for asking!",
            "what is your name": f"My name is {self.name}.",
            "time": f"The time is {self._get_time('time')}.",
            "date": f"Today's date is {self._get_date('date')}.",
        }
        
        for key, response in responses.items():
            if key in text_lower:
                return response
        
        return "I'm not sure how to respond to that. Say 'help' for things I can do."
    
    # Tool implementations
    def _get_time(self, *args) -> str:
        """Get current time."""
        from datetime import datetime
        return datetime.now().strftime("%I:%M %p")
    
    def _get_date(self, *args) -> str:
        """Get current date."""
        from datetime import datetime
        return datetime.now().strftime("%B %d, %Y")
    
    def _help(self, *args) -> str:
        """Get help."""
        tools = ", ".join(self.tools.keys())
        return f"I can help with: {tools}. Just ask!"
    
    def stop(self):
        """Stop the agent."""
        self.is_running = False
    
    def add_tool(self, name: str, func: Callable):
        """Add a custom tool."""
        self.tools[name] = func
    
    def get_status(self) -> dict:
        """Get agent status."""
        return {
            "name": self.name,
            "is_running": self.is_running,
            "tools": list(self.tools.keys()),
        }


def create_agent(**kwargs) -> VoiceAgent:
    """Create a VoiceAgent instance."""
    return VoiceAgent(**kwargs)
