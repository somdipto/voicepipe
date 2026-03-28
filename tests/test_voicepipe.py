"""
VoicePipe Tests - Clean Architecture
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
        from voicepipe.tts import TTS
        assert TTS is not None
    
    def test_tts_init(self):
        """Test TTS initialization."""
        from voicepipe.tts import TTS
        tts = TTS()
        assert tts is not None
        assert tts.backend is not None
    
    def test_tts_empty_text(self):
        """Test TTS rejects empty text."""
        from voicepipe.tts import TTS
        tts = TTS()
        with pytest.raises(ValueError):
            tts.speak("")
    
    def test_tts_valid_text(self):
        """Test TTS works with valid text."""
        from voicepipe.tts import TTS
        tts = TTS()
        audio = tts.speak("Hello world")
        assert audio is not None
        assert len(audio) > 0
    
    def test_tts_save_to_file(self):
        """Test TTS to file."""
        from voicepipe.tts import TTS
        tts = TTS()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
        
        try:
            result = tts.save("Test", temp_path)
            assert os.path.exists(result)
            assert os.path.getsize(result) > 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_list_voices(self):
        """Test listing voices."""
        from voicepipe.tts import TTS
        tts = TTS()
        voices = tts.list_voices()
        assert voices is not None
        assert len(voices) > 0
    
    def test_detect_tts(self):
        """Test TTS detection."""
        from voicepipe.tts import detect_tts
        result = detect_tts()
        assert result is not None


class TestSTT:
    """Test Speech-to-Text functionality."""
    
    def test_stt_import(self):
        """Test STT can be imported."""
        from voicepipe.stt import STT
        assert STT is not None
    
    def test_detect_stt(self):
        """Test STT detection."""
        from voicepipe.stt import detect_stt
        result = detect_stt()
        assert result is not None


class TestInstaller:
    """Test Installer."""
    
    def test_installer_import(self):
        """Test Installer can be imported."""
        from voicepipe.installer import install_all
        assert install_all is not None
    
    def test_check_status(self):
        """Test status check."""
        from voicepipe.installer import check_status
        status = check_status()
        assert isinstance(status, dict)
        assert "stt" in status
        assert "tts" in status


class TestCLI:
    """Test CLI functionality."""
    
    def test_cli_import(self):
        """Test CLI can be imported."""
        from voicepipe.cli import main
        assert main is not None


class TestVoicePipe:
    """Test main VoicePipe module."""
    
    def test_version(self):
        """Test version."""
        from voicepipe import __version__
        assert __version__ == "1.1.0"
    
    def test_lazy_tts(self):
        """Test lazy TTS import."""
        from voicepipe import create_tts
        speaker = create_tts()
        assert speaker is not None
    
    def test_lazy_stt(self):
        """Test lazy STT import."""
        from voicepipe import create_stt
        listener = create_stt()
        assert listener is not None
    
    def test_status(self):
        """Test status function."""
        from voicepipe import status
        result = status()
        assert isinstance(result, dict)
        assert "stt" in result
        assert "tts" in result
        assert "version" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])