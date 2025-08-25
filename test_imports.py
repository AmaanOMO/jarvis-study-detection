#!/usr/bin/env python3
"""
Test script to verify all imports work correctly.
Run this before running the main application.
"""

def test_imports():
    """Test all required imports."""
    print("🧪 Testing imports...")
    
    try:
        import cv2
        print("✅ OpenCV imported successfully")
    except ImportError as e:
        print(f"❌ OpenCV import failed: {e}")
        return False
    
    try:
        import mediapipe as mp
        print("✅ MediaPipe imported successfully")
    except ImportError as e:
        print(f"❌ MediaPipe import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ NumPy imported successfully")
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    try:
        from elevenlabs import generate, set_api_key
        print("✅ ElevenLabs imported successfully")
    except ImportError as e:
        print(f"❌ ElevenLabs import failed: {e}")
        return False
    
    try:
        import simpleaudio as sa
        print("✅ SimpleAudio imported successfully")
    except ImportError as e:
        print(f"❌ SimpleAudio import failed: {e}")
        return False
    
    try:
        import soundfile as sf
        print("✅ SoundFile imported successfully")
    except ImportError as e:
        print(f"❌ SoundFile import failed: {e}")
        return False
    
    # Test local imports
    try:
        from gaze import GazeDetector
        print("✅ Local gaze module imported successfully")
    except ImportError as e:
        print(f"❌ Local gaze module import failed: {e}")
        return False
    
    try:
        from logic import FocusLogic
        print("✅ Local logic module imported successfully")
    except ImportError as e:
        print(f"❌ Local logic module import failed: {e}")
        return False
    
    try:
        from tts import TTSManager
        print("✅ Local TTS module imported successfully")
    except ImportError as e:
        print(f"❌ Local TTS module import failed: {e}")
        return False
    
    try:
        from bubble import VoiceBubble
        print("✅ Local bubble module imported successfully")
    except ImportError as e:
        print(f"❌ Local bubble module import failed: {e}")
        return False
    
    print("\n🎉 All imports successful! You're ready to run the app.")
    return True

if __name__ == "__main__":
    test_imports()
