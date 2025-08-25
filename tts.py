import os
import io
import numpy as np
import soundfile as sf
import simpleaudio as sa
from elevenlabs import generate, set_api_key
from typing import Tuple, Optional
import threading
import time

class TTSManager:
    def __init__(self, api_key: str, voice_id: str, model: str = "eleven_multilingual_v2"):
        """
        Initialize TTS manager with ElevenLabs credentials.
        
        Args:
            api_key: ElevenLabs API key
            voice_id: Voice ID to use for TTS
            model: TTS model to use
        """
        self.api_key = api_key
        self.voice_id = voice_id
        self.model = model
        
        # Set API key
        set_api_key(api_key)
        
        # Audio playback state
        self.current_audio: Optional[np.ndarray] = None
        self.current_envelope: Optional[np.ndarray] = None
        self.is_playing = False
        self.playback_thread: Optional[threading.Thread] = None
        
        # Default voice settings
        self.voice_settings = {
            "stability": 0.5,
            "similarity_boost": 0.7,
            "style": 0.3
        }
    
    def update_voice_settings(self, stability: float = None, 
                            similarity_boost: float = None, 
                            style: float = None):
        """Update voice settings."""
        if stability is not None:
            self.voice_settings["stability"] = stability
        if similarity_boost is not None:
            self.voice_settings["similarity_boost"] = similarity_boost
        if style is not None:
            self.voice_settings["style"] = style
    
    def synth(self, text: str, speaking_rate: float = 1.2) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Synthesize text to speech and compute audio envelope.
        
        Args:
            text: Text to synthesize
            speaking_rate: Speed multiplier (0.5 to 2.0)
            
        Returns:
            Tuple of (audio_samples, envelope, duration_seconds)
        """
        try:
            # Generate audio using ElevenLabs
            audio = generate(
                text=text,
                voice=self.voice_id,
                model=self.model,
                voice_settings=self.voice_settings
            )
            
            # Convert to numpy array
            audio_array, sample_rate = sf.read(io.BytesIO(audio))
            
            # Apply speaking rate by resampling
            if speaking_rate != 1.0:
                audio_array = self._resample_audio(audio_array, sample_rate, speaking_rate)
                # Adjust sample rate for duration calculation
                sample_rate = sample_rate * speaking_rate
            
            # Compute audio envelope
            envelope = self._compute_envelope(audio_array, sample_rate)
            
            # Calculate duration
            duration = len(audio_array) / sample_rate
            
            return audio_array, envelope, duration
            
        except Exception as e:
            print(f"TTS synthesis failed: {e}")
            # Return silence
            sample_rate = 22050
            duration = 1.0
            audio_array = np.zeros(int(sample_rate * duration))
            envelope = np.zeros(50)  # 50 envelope points
            return audio_array, envelope, duration
    
    def _resample_audio(self, audio: np.ndarray, sample_rate: int, rate_multiplier: float) -> np.ndarray:
        """Simple resampling by interpolation."""
        if rate_multiplier == 1.0:
            return audio
        
        # Calculate new length
        new_length = int(len(audio) / rate_multiplier)
        
        # Create time arrays
        old_time = np.linspace(0, 1, len(audio))
        new_time = np.linspace(0, 1, new_length)
        
        # Interpolate
        resampled = np.interp(new_time, old_time, audio)
        
        return resampled
    
    def _compute_envelope(self, audio: np.ndarray, sample_rate: int, 
                         frame_duration_ms: float = 20.0) -> np.ndarray:
        """
        Compute audio envelope for visualization.
        
        Args:
            audio: Audio samples
            sample_rate: Sample rate in Hz
            frame_duration_ms: Duration of each envelope frame in milliseconds
            
        Returns:
            Array of envelope values (0.0 to 1.0)
        """
        frame_samples = int(sample_rate * frame_duration_ms / 1000.0)
        num_frames = len(audio) // frame_samples
        
        envelope = []
        for i in range(num_frames):
            start = i * frame_samples
            end = start + frame_samples
            frame = audio[start:end]
            
            # Compute RMS for this frame
            rms = np.sqrt(np.mean(frame ** 2))
            envelope.append(rms)
        
        # Normalize to 0-1 range
        if envelope:
            max_val = max(envelope)
            if max_val > 0:
                envelope = [e / max_val for e in envelope]
        
        return np.array(envelope)
    
    def play(self, audio: np.ndarray, sample_rate: int = 22050) -> bool:
        """
        Play audio non-blocking.
        
        Args:
            audio: Audio samples to play
            sample_rate: Sample rate in Hz
            
        Returns:
            True if playback started successfully
        """
        try:
            # Stop any current playback
            self.stop()
            
            # Store current audio and envelope
            self.current_audio = audio
            self.current_envelope = self._compute_envelope(audio, sample_rate)
            
            # Start playback in separate thread
            self.playback_thread = threading.Thread(
                target=self._playback_worker,
                args=(audio, sample_rate)
            )
            self.playback_thread.daemon = True
            self.playback_thread.start()
            
            self.is_playing = True
            return True
            
        except Exception as e:
            print(f"Audio playback failed: {e}")
            return False
    
    def _playback_worker(self, audio: np.ndarray, sample_rate: int):
        """Worker thread for audio playback."""
        try:
            # Ensure audio is in correct format
            if audio.dtype != np.int16:
                # Convert to 16-bit PCM
                audio_16bit = (audio * 32767).astype(np.int16)
            else:
                audio_16bit = audio
            
            # Play audio
            play_obj = sa.play_buffer(audio_16bit, 1, 2, sample_rate)
            play_obj.wait_done()
            
        except Exception as e:
            print(f"Playback worker error: {e}")
        finally:
            self.is_playing = False
    
    def stop(self):
        """Stop current audio playback."""
        self.is_playing = False
        if self.playback_thread and self.playback_thread.is_alive():
            # Wait a bit for thread to finish
            self.playback_thread.join(timeout=0.1)
    
    def is_playing_audio(self) -> bool:
        """Check if audio is currently playing."""
        return self.is_playing
    
    def get_current_envelope(self) -> Optional[np.ndarray]:
        """Get envelope of currently playing audio."""
        return self.current_envelope
    
    def get_playback_progress(self) -> float:
        """Get playback progress as 0.0 to 1.0."""
        if not self.is_playing or self.current_audio is None:
            return 0.0
        
        # This is a simplified progress calculation
        # In a real implementation, you'd track actual playback position
        return 0.5  # Placeholder
    
    def cleanup(self):
        """Clean up resources."""
        self.stop()
        if self.current_audio is not None:
            self.current_audio = None
        if self.current_envelope is not None:
            self.current_envelope = None
