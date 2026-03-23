"""
VoicePipe Tests - Comprehensive Test Suite
"""
import pytest
import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestTTS:
    """Test Text-to-Speech functionality."""
    
    def test_tts_import(self):
        """Test TTS can be imported."""
        from voicepipe.tts import TTSEngine
        assert TTSEngine is not None
    
    def test_tts_init(self):
        """Test TTS initialization."""
        from voicepipe.tts import TTSEngine
        tts = TTSEngine()
        assert tts is not None
        assert tts.backend is not None
    
    def test_tts_empty_text(self):
        """Test TTS rejects empty text."""
        from voicepipe.tts import TTSEngine, TTSError
        tts = TTSEngine()
        with pytest.raises(TTSError):
            tts.speak("")
    
    def test_tts_whitespace_only(self):
        """Test TTS rejects whitespace-only text."""
        from voicepipe.tts import TTSEngine, TTSError
        tts = TTSEngine()
        with pytest.raises(TTSError):
            tts.speak("   ")
    
    def test_tts_valid_text(self):
        """Test TTS works with valid text."""
        from voicepipe.tts import TTSEngine
        tts = TTSEngine()
        audio = tts.speak("Hello world")
        assert audio is not None
        assert len(audio) > 0
    
    def test_tts_speak_to_file(self):
        """Test TTS to file."""
        from voicepipe.tts import TTSEngine
        tts = TTSEngine()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
        
        try:
            result = tts.speak_to_file("Test", temp_path)
            assert os.path.exists(result)
            assert os.path.getsize(result) > 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_list_voices(self):
        """Test listing voices."""
        from voicepipe.tts import TTSEngine
        tts = TTSEngine()
        voices = tts.list_voices()
        assert voices is not None
        assert len(voices) > 0
    
    def test_check_tts_available(self):
        """Test TTS availability check."""
        from voicepipe.tts import check_tts_available
        result = check_tts_available()
        assert isinstance(result, dict)
        assert "gtts" in result


class TestSTT:
    """Test Speech-to-Text functionality."""
    
    def test_stt_import(self):
        """Test STT can be imported."""
        from voicepipe.stt import STTEngine
        assert STTEngine is not None
    
    def test_check_stt_available(self):
        """Test STT availability check."""
        from voicepipe.stt import check_stt_available
        result = check_stt_available()
        assert isinstance(result, dict)
        assert "whisper_found" in result
        assert "ffmpeg_found" in result


class TestInstaller:
    """Test Auto-Installer."""
    
    def test_installer_import(self):
        """Test Installer can be imported."""
        from voicepipe.installer import AutoInstaller
        assert AutoInstaller is not None
    
    def test_installer_init(self):
        """Test Installer initialization."""
        from voicepipe.installer import AutoInstaller
        installer = AutoInstaller()
        assert installer is not None
        assert installer.cache_dir is not None
    
    def test_check_status(self):
        """Test status check."""
        from voicepipe.installer import AutoInstaller
        installer = AutoInstaller()
        status = installer.check_status()
        assert isinstance(status, dict)
        assert "os" in status
        assert "ffmpeg" in status
        assert "whisper" in status


class TestVoicePipeline:
    """Test VoicePipeline integration."""
    
    def test_pipeline_import(self):
        """Test pipeline can be imported."""
        from voicepipe import VoicePipeline
        assert VoicePipeline is not None
    
    def test_pipeline_init(self):
        """Test pipeline initialization."""
        from voicepipe import VoicePipeline
        vp = VoicePipeline(auto_install=False)
        assert vp is not None
    
    def test_pipeline_status(self):
        """Test pipeline status."""
        from voicepipe import VoicePipeline
        vp = VoicePipeline(auto_install=False)
        status = vp.check_status()
        assert isinstance(status, dict)
    
    def test_tts_works(self):
        """Test pipeline TTS works."""
        from voicepipe import VoicePipeline
        vp = VoicePipeline()
        audio = vp.text_to_speech("test")
        assert audio is not None
        assert len(audio) > 0


class TestCLI:
    """Test CLI functionality."""
    
    def test_cli_import(self):
        """Test CLI can be imported."""
        from voicepipe.cli import main
        assert main is not None


class TestAgent:
    """Test VoiceAgent."""
    
    def test_agent_import(self):
        """Test agent can be imported."""
        from voicepipe.agent import VoiceAgent
        assert VoiceAgent is not None
    
    def test_agent_init(self):
        """Test agent initialization."""
        from voicepipe import VoicePipeline
        from voicepipe.agent import VoiceAgent
        
        vp = VoicePipeline(auto_install=False)
        agent = VoiceAgent(voice_pipeline=vp)
        assert agent is not None
        assert agent.name == "VoiceAgent"
    
    def test_agent_status(self):
        """Test agent status."""
        from voicepipe import VoicePipeline
        from voicepipe.agent import VoiceAgent
        
        vp = VoicePipeline(auto_install=False)
        agent = VoiceAgent(voice_pipeline=vp)
        status = agent.get_status()
        assert isinstance(status, dict)
        assert "name" in status
        assert "is_running" in status
    
    def test_agent_tools(self):
        """Test agent has tools."""
        from voicepipe import VoicePipeline
        from voicepipe.agent import VoiceAgent
        
        vp = VoicePipeline(auto_install=False)
        agent = VoiceAgent(voice_pipeline=vp)
        assert "time" in agent.tools
        assert "date" in agent.tools


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
