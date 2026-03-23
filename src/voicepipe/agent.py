"""
Voice Agent - Continuous voice interaction agent

The brain of VoicePipe. Handles:
- Continuous listening
- Intent recognition
- Tool execution
- Memory and context

Usage:
    from voicepipe.agent import VoiceAgent
    agent = VoiceAgent()
    await agent.run()
"""
import asyncio
import logging
import os
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger("voicepipe.agent")

# Default system prompt
DEFAULT_SYSTEM_PROMPT = """You are VoiceAgent, a helpful voice assistant.

You can:
- Answer questions
- Control applications
- Send messages
- Make calls
- Set reminders
- And much more

Always be helpful, concise, and friendly.
"""


class VoiceAgent:
    """
    Continuous voice agent.
    
    Usage:
        from voicepipe.agent import VoiceAgent
        agent = VoiceAgent()
        await agent.run()
    """
    
    def __init__(
        self,
        name: str = "VoiceAgent",
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        voice_pipeline = None,
        auto_listen: bool = True,
    ):
        """
        Initialize VoiceAgent.
        
        Args:
            name: Agent name
            system_prompt: System prompt
            voice_pipeline: VoicePipeline instance (optional)
            auto_listen: Automatically listen after responding
        """
        self.name = name
        self.system_prompt = system_prompt
        self.auto_listen = auto_listen
        
        # Initialize voice pipeline
        if voice_pipeline is None:
            from voicepipe import VoicePipeline
            self.voice = VoicePipeline()
        else:
            self.voice = voice_pipeline
        
        # State
        self.is_running = False
        self.context = []
        self.tools = {}
        
        # Register default tools
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools."""
        self.tools = {
            "time": self._get_time,
            "date": self._get_date,
            "weather": self._get_weather,
            "search": self._search_web,
            "open_app": self._open_app,
            "calculate": self._calculate,
        }
    
    async def run(self):
        """Run the agent loop."""
        self.is_running = True
        
        logger.info(f"{self.name} started. Say 'exit' to quit.")
        
        while self.is_running:
            try:
                # Listen for audio
                audio = await self.listen()
                
                if audio is None:
                    continue
                
                # Convert to text
                text = self.voice.speech_to_text_bytes(audio)
                
                if not text.strip():
                    continue
                
                logger.info(f"You: {text}")
                
                # Check for exit
                if text.lower() in ["exit", "quit", "bye"]:
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
        Listen for audio input.
        
        Override this method to implement custom listening.
        """
        # This is a placeholder - implement microphone input
        # For now, return None (no auto-listening)
        return None
    
    async def speak(self, text: str):
        """
        Speak the response.
        
        Args:
            text: Text to speak
        """
        try:
            audio = self.voice.text_to_speech(text)
            # Play audio (implementation depends on platform)
            logger.info(f"{self.name}: {text}")
        except Exception as e:
            logger.error(f"TTS failed: {e}")
    
    async def respond(self, text: str) -> str:
        """
        Process input and generate response.
        
        Args:
            text: Input text
            
        Returns:
            Response text
        """
        # Simple rule-based responses
        # In production, this would use an LLM
        
        text_lower = text.lower()
        
        # Check registered tools
        for tool_name, tool_func in self.tools.items():
            if tool_name in text_lower:
                try:
                    result = await tool_func(text)
                    return result
                except Exception as e:
                    return f"Error: {e}"
        
        # Default responses
        responses = {
            "hello": "Hello! How can I help you?",
            "hi": "Hi there! What can I do for you?",
            "how are you": "I'm doing great, thanks for asking!",
            "what is your name": f"My name is {self.name}.",
            "time": f"The time is {self._get_time()}.",
            "date": f"Today's date is {self._get_date()}.",
        }
        
        for key, response in responses.items():
            if key in text_lower:
                return response
        
        # Default
        return "I'm not sure how to respond to that. Could you try again?"
    
    # Tool implementations
    def _get_time(self) -> str:
        """Get current time."""
        from datetime import datetime
        return datetime.now().strftime("%I:%M %p")
    
    def _get_date(self) -> str:
        """Get current date."""
        from datetime import datetime
        return datetime.now().strftime("%B %d, %Y")
    
    async def _get_weather(self, text: str) -> str:
        """Get weather information."""
        return "Weather feature coming soon!"
    
    async def _search_web(self, text: str) -> str:
        """Search the web."""
        return "Web search coming soon!"
    
    async def _open_app(self, text: str) -> str:
        """Open an application."""
        return "App control coming soon!"
    
    async def _calculate(self, text: str) -> str:
        """Calculate something."""
        # Extract math expression
        import re
        match = re.search(r'[\d+\-*/()]+', text)
        if match:
            try:
                result = eval(match.group())
                return f"The answer is {result}"
            except:
                pass
        return "I couldn't understand the calculation."
    
    def stop(self):
        """Stop the agent."""
        self.is_running = False
    
    def add_tool(self, name: str, func):
        """Add a custom tool."""
        self.tools[name] = func
    
    def get_status(self) -> dict:
        """Get agent status."""
        return {
            "name": self.name,
            "is_running": self.is_running,
            "context_length": len(self.context),
            "tools": list(self.tools.keys()),
        }


class SimpleVoiceAgent(VoiceAgent):
    """Simple CLI-based voice agent for testing."""
    
    async def listen(self) -> Optional[bytes]:
        """Listen via CLI input."""
        # For testing - use CLI input instead of microphone
        text = input("\nYou: ")
        
        # Convert to audio placeholder
        # In real implementation, would use TTS
        return None


def create_agent(**kwargs) -> VoiceAgent:
    """Create a VoiceAgent instance."""
    return VoiceAgent(**kwargs)
