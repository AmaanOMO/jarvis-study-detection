# Jarvis Study Detection 🎯

A minimal Mac-friendly Python app that detects when you're not looking at the screen and roasts you with ElevenLabs TTS to keep you focused on your studies.

## Features ✨

- **Eye Tracking**: Uses MediaPipe Face Mesh to detect gaze direction and head pose
- **Smart Detection**: Triggers roasts only after sustained distraction (configurable hold time)
- **ElevenLabs TTS**: High-quality voice synthesis with customizable roast lines
- **Animated UI**: Voice bubble with pulse animation and typewriter text effects
- **Event Logging**: CSV logging of all events for analysis
- **Hotkey Controls**: Space (toggle), R (reset), Q (quit)

## Requirements 🖥️

- macOS (tested on macOS 14+)
- Python 3.8+
- Webcam
- ElevenLabs API key and voice ID

## Installation 🚀

1. **Clone the repository**
   ```bash
   git clone https://github.com/Amaansheikh/jarvis-study-detection.git
   cd jarvis-study-detection
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure ElevenLabs**
   - Get your API key from [ElevenLabs](https://elevenlabs.io/)
   - Get your voice ID from the ElevenLabs dashboard
   - Update `config.json` with your voice ID
   - Set environment variable:
     ```bash
     export ELEVEN_API_KEY='your_api_key_here'
     ```

## Configuration ⚙️

Edit `config.json` to customize:

- **Video settings**: Window size, camera area
- **Detection thresholds**: Yaw/pitch limits, gaze ratios, timing
- **TTS settings**: Voice parameters, speaking rate
- **Roast lines**: Custom messages to keep you focused

### Example config.json
```json
{
  "video": { 
    "width": 1280, 
    "height": 720, 
    "cam_width": 840 
  },
  "thresholds": {
    "yaw_deg": 20.0,
    "pitch_deg": 15.0,
    "gaze_center_min": 0.35,
    "gaze_center_max": 0.65,
    "away_hold_s": 0.6,
    "cooldown_s": 2.0
  },
  "tts": {
    "voice_id": "YOUR_VOICE_ID_HERE",
    "speaking_rate": 1.2,
    "model": "eleven_multilingual_v2"
  },
  "lines": [
    "You're not Iron-Man lil bro",
    "Lock in. The code won't write itself.",
    "Attention drift detected. Return to your work."
  ]
}
```

## Usage 🎮

1. **Start the app**
   ```bash
   python main.py
   ```

2. **Controls**
   - **Space**: Toggle system active/inactive
   - **R**: Reset cooldown timer
   - **Q**: Quit application
   - **Click bubble**: Force speak default roast

3. **How it works**
   - Look at the screen → Status shows "LOOKING"
   - Look away for 0.6s → Status shows "AWAY" and roast plays
   - Voice bubble animates while speaking
   - Events logged to `logs/events.csv`

## Project Structure 📁

```
jarvis_focus/
├── main.py          # Main application and video loop
├── gaze.py          # MediaPipe gaze detection
├── logic.py         # Focus logic and state machine
├── tts.py           # ElevenLabs TTS integration
├── bubble.py        # Voice bubble UI and animations
├── config.json      # Configuration file
├── requirements.txt # Python dependencies
└── logs/            # Event logs (auto-created)
    └── events.csv   # CSV log of all events
```

## Technical Details 🔧

### Gaze Detection
- **MediaPipe Face Mesh** with `refine_landmarks=True`
- **Head pose estimation** using solvePnP (yaw/pitch)
- **Iris tracking** for horizontal gaze ratio
- **Configurable thresholds** for detection sensitivity

### TTS Integration
- **ElevenLabs API** for high-quality voice synthesis
- **Audio envelope computation** for UI animation
- **Non-blocking playback** with threading
- **Speaking rate control** (0.5x to 2.0x)

### UI Design
- **High-contrast colors** optimized for phone recording
- **1280x720 window** with camera left, bubble right
- **Animated voice bubble** with pulse and typewriter effects
- **Real-time status display** with metrics overlay

## Troubleshooting 🛠️

### Common Issues

1. **"Failed to open webcam"**
   - Check camera permissions in System Preferences
   - Ensure no other app is using the camera

2. **"TTS synthesis failed"**
   - Verify ElevenLabs API key is set correctly
   - Check voice ID in config.json
   - Ensure internet connection

3. **Poor detection accuracy**
   - Adjust thresholds in config.json
   - Ensure good lighting
   - Position face clearly in camera view

### Performance Tips

- **Lower camera resolution** if experiencing lag
- **Adjust hold times** for your attention patterns
- **Use SSD** for faster audio processing

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License 📄

This project is open source. Feel free to use and modify for your own study sessions!

## Acknowledgments 🙏

- **MediaPipe** for facial landmark detection
- **ElevenLabs** for high-quality TTS
- **OpenCV** for computer vision capabilities

---

**Stay focused, stay productive! 💪**

*Built with ❤️ for productive study sessions*
