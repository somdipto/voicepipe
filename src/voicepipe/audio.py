"""
Audio utilities for VoicePipe
"""
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Optional


class AudioUtils:
    """Audio processing utilities."""
    
    @staticmethod
    def convert_audio(
        input_path: str,
        output_path: str,
        sample_rate: int = 16000,
        mono: bool = True,
        format: str = "wav",
    ) -> str:
        """
        Convert audio file to different format.
        
        Args:
            input_path: Input audio file
            output_path: Output audio file
            sample_rate: Target sample rate
            mono: Convert to mono
            format: Output format
            
        Returns:
            Path to converted file
        """
        mono_arg = "-ac 1" if mono else ""
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-ar", str(sample_rate),
            mono_arg,
            f"-c:a", "pcm_s16le" if format == "wav" else format,
            output_path,
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Audio conversion failed: {result.stderr}")
        
        return output_path
    
    @staticmethod
    def get_audio_duration(audio_path: str) -> float:
        """Get duration of audio file in seconds."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to get duration: {result.stderr}")
        
        return float(result.stdout.strip())
    
    @staticmethod
    def normalize_audio(input_path: str, output_path: str) -> str:
        """Normalize audio volume."""
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            output_path,
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Audio normalization failed: {result.stderr}")
        
        return output_path
    
    @staticmethod
    def trim_silence(
        input_path: str,
        output_path: str,
        threshold: float = -40,
        min_duration: float = 0.5,
    ) -> str:
        """Trim silence from audio."""
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-af", f"silenceremove=start_periods=1:start_duration={min_duration}:start_threshold={threshold}dB:detection=speech",
            output_path,
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Silence trim failed: {result.stderr}")
        
        return output_path
    
    @staticmethod
    def split_stereo(input_path: str) -> tuple:
        """Split stereo audio to two mono files."""
        left_path = input_path.replace(".wav", "_left.wav")
        right_path = input_path.replace(".wav", "_right.wav")
        
        # Left channel
        subprocess.run([
            "ffmpeg", "-y", "-i", input_path,
            "-af", "pan=mono|c0=c0",
            left_path
        ], capture_output=True)
        
        # Right channel
        subprocess.run([
            "ffmpeg", "-y", "-i", input_path,
            "-af", "pan=mono|c0=c1",
            right_path
        ], capture_output=True)
        
        return left_path, right_path
    
    @staticmethod
    def concatenate_audio(audio_files: list, output_path: str) -> str:
        """Concatenate multiple audio files."""
        # Create file list
        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as f:
            for audio_file in audio_files:
                f.write(f"file '{audio_file}'\n")
            list_path = f.name
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_path,
            "-c", "copy",
            output_path,
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        os.unlink(list_path)
        
        if result.returncode != 0:
            raise RuntimeError(f"Audio concatenation failed: {result.stderr}")
        
        return output_path