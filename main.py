#!/usr/bin/env python3
"""
Jarvis Study Detection - Main Application
A minimal Mac-friendly Python app that detects when you're not looking at the screen
and roasts you with ElevenLabs TTS.
"""

import cv2
import json
import os
import time
import csv
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, continue without it
    pass

# Local imports
from gaze import GazeDetector
from logic import FocusLogic
from tts import TTSManager
from bubble import VoiceBubble
from hud import JarvisHUD
from ws_bridge import start_ws_server_in_thread, broadcast, on_click

class JarvisApp:
    def __init__(self, config_path: str = "config.json"):
        """Initialize the Jarvis application."""
        self.config = self._load_config(config_path)
        self.running = False
        
        # Initialize components
        self.gaze_detector = GazeDetector()
        self.focus_logic = FocusLogic(
            away_hold_s=self.config['thresholds']['away_hold_s'],
            cooldown_s=self.config['thresholds']['cooldown_s']
        )
        
        # TTS will be initialized when API key is provided
        self.tts_manager: Optional[TTSManager] = None
        
        # UI components
        self.bubble = VoiceBubble(
            width=self.config['video']['width'] - self.config['video']['cam_width'],
            height=self.config['video']['height']
        )
        
        # Initialize HUD
        self.hud = JarvisHUD(
            width=self.config['video']['width'] - self.config['video']['cam_width'],
            height=self.config['video']['height'],
            config=self.config
        )
        
        # Video capture
        self.cap: Optional[cv2.VideoCapture] = None
        
        # State
        self.current_roast_index = 0
        self.speaking_start_time = 0
        self.current_envelope: Optional[list] = None
        self.last_spoken_line = ""
        
        # Logging
        self.logs_dir = "logs"
        self._ensure_logs_dir()
        
        # Update thresholds
        self.gaze_detector.update_thresholds(
            self.config['thresholds']['yaw_deg'],
            self.config['thresholds']['pitch_deg'],
            self.config['thresholds']['gaze_center_min'],
            self.config['thresholds']['gaze_center_max']
        )
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Validate required fields
            required_fields = ['video', 'thresholds', 'tts', 'lines']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required config field: {field}")
            
            return config
            
        except FileNotFoundError:
            print(f"Config file not found: {config_path}")
            print("Please create config.json with your ElevenLabs API key and voice ID")
            exit(1)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in config file: {e}")
            exit(1)
        except ValueError as e:
            print(f"Config validation error: {e}")
            exit(1)
    
    def _ensure_logs_dir(self):
        """Ensure logs directory exists."""
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
    
    def _log_event(self, event: str, message: str, status: str = ""):
        """Log an event to CSV file."""
        timestamp = datetime.now().isoformat()
        status = status or self.focus_logic.get_status()
        
        log_file = os.path.join(self.logs_dir, "events.csv")
        file_exists = os.path.exists(log_file)
        
        with open(log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['timestamp', 'status', 'event', 'message'])
            writer.writerow([timestamp, status, event, message])
    
    def initialize_tts(self):
        """Initialize TTS manager with API credentials."""
        voice_id = self.config['tts']['voice_id']
        
        if voice_id == "REPLACE_ME_WITH_YOUR_VOICE_ID":
            print("⚠️  Please update config.json with your ElevenLabs VOICE_ID")
            print("   You can find your voice ID in the ElevenLabs dashboard")
            return False
        
        # Check for API key in environment
        api_key = os.getenv('ELEVEN_API_KEY')
        if not api_key:
            print("⚠️  Please set ELEVEN_API_KEY environment variable")
            print("   export ELEVEN_API_KEY='ELEVEN_API_KEY'")
            return False
        
        try:
            self.tts_manager = TTSManager(
                api_key=api_key,
                voice_id=voice_id,
                model=self.config['tts']['model']
            )
            
            # Update voice settings
            self.tts_manager.update_voice_settings(
                stability=self.config['tts']['stability'],
                similarity_boost=self.config['tts']['similarity_boost'],
                style=self.config['tts']['style']
            )
            
            print("✅ TTS initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize TTS: {e}")
            return False
    
    def start_video_capture(self):
        """Initialize video capture."""
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            print("❌ Failed to open webcam")
            return False
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("✅ Video capture initialized")
        return True
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Process a single frame and return the composed output."""
        # Mirror the frame
        frame = cv2.flip(frame, 1)
        
        # Detect gaze
        gaze_result = self.gaze_detector.detect(frame)
        is_away = gaze_result['status'] == 'AWAY'
        
        # Update focus logic
        roast_event = self.focus_logic.update(is_away)
        
        # Handle roast event
        if roast_event == 'ROAST' and self.focus_logic.is_active() and self.tts_manager:
            self._trigger_roast()
        
        # Resize frame to fit left side
        cam_width = self.config['video']['cam_width']
        cam_height = self.config['video']['height']
        
        # Resize frame to fit camera area while maintaining aspect ratio
        frame_h, frame_w = frame.shape[:2]
        aspect_ratio = frame_w / frame_h
        target_aspect = cam_width / cam_height
        
        if aspect_ratio > target_aspect:
            # Frame is wider, fit to height
            new_h = cam_height
            new_w = int(cam_height * aspect_ratio)
        else:
            # Frame is taller, fit to width
            new_w = cam_width
            new_h = int(cam_width / aspect_ratio)
        
        resized_frame = cv2.resize(frame, (new_w, new_h))
        
        # Create canvas
        canvas = np.zeros((cam_height, self.config['video']['width'], 3), dtype=np.uint8)
        
        # Place camera frame on left side
        y_offset = (cam_height - new_h) // 2
        x_offset = (cam_width - new_w) // 2
        
        # Ensure offsets are within bounds
        y_offset = max(0, min(y_offset, cam_height - new_h))
        x_offset = max(0, min(x_offset, cam_width - new_w))
        
        # Ensure we don't exceed canvas bounds
        end_y = min(y_offset + new_h, cam_height)
        end_x = min(x_offset + new_w, cam_width)
        
        canvas[y_offset:end_y, x_offset:end_x] = resized_frame[:end_y-y_offset, :end_x-x_offset]
        
        # Add HUD overlay on camera
        self._draw_camera_hud(canvas, gaze_result)
        
        # Place HUD on right side
        hud_canvas = canvas[:, cam_width:]
        
        # Calculate pulse from audio envelope
        pulse = 0.0
        if (self.tts_manager and 
            hasattr(self.tts_manager, 'is_playing') and 
            self.tts_manager.is_playing and 
            self.current_envelope is not None):
            current_time = time.time()
            progress = (current_time - self.speaking_start_time) / 2.0  # Approximate duration
            if 0 <= progress <= 1:
                envelope_index = int(progress * len(self.current_envelope))
                if envelope_index < len(self.current_envelope):
                    pulse = self.current_envelope[envelope_index]
        
        # Draw HUD
        hud_output = self.hud.draw(hud_canvas, gaze_result['status'], 
                                  self.last_spoken_line, pulse, 0.016)  # ~60 FPS
        canvas[:, cam_width:] = hud_output
        
        return canvas
    
    def _draw_camera_hud(self, canvas: np.ndarray, gaze_result: Dict[str, Any]):
        """Draw HUD overlay on camera feed."""
        # Status text
        status = gaze_result['status']
        status_color = (0, 255, 0) if status == 'LOOKING' else (0, 0, 255)
        
        cv2.putText(canvas, f"Status: {status}", (20, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Gaze metrics
        cv2.putText(canvas, f"Yaw: {gaze_result['yaw']:.1f}°", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(canvas, f"Pitch: {gaze_result['pitch']:.1f}°", (20, 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(canvas, f"Gaze: {gaze_result['gaze_ratio']:.2f}", (20, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Away duration
        away_duration = self.focus_logic.get_away_duration()
        if away_duration > 0:
            cv2.putText(canvas, f"Away: {away_duration:.1f}s", (20, 135),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
        
        # System status
        system_status = "ACTIVE" if self.focus_logic.is_active() else "INACTIVE"
        status_color = (0, 255, 0) if self.focus_logic.is_active() else (128, 128, 128)
        cv2.putText(canvas, f"System: {system_status}", (20, 160),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 1)
    
    def _trigger_roast(self):
        """Trigger a roast from the configured lines."""
        if not self.tts_manager or not self.config['lines']:
            return
        
        # Get next roast line
        roast_line = self.config['lines'][self.current_roast_index]
        self.current_roast_index = (self.current_roast_index + 1) % len(self.config['lines'])
        
        # Add some Jarvis personality with random witty suffixes
        roast_line = self._add_jarvis_personality(roast_line)
        
        # Add context-aware commentary based on away duration
        away_duration = self.focus_logic.get_away_duration()
        roast_line = self._add_context_awareness(roast_line, away_duration)
        
        # Set bubble text
        self.bubble.set_text(roast_line)
        
        # Synthesize and play
        try:
            audio, envelope, duration, sample_rate = self.tts_manager.synth(
                roast_line,
                self.config['tts']['speaking_rate']
            )
            
            if self.tts_manager.play(audio, sample_rate=sample_rate):
                self.speaking_start_time = time.time()
                self.current_envelope = envelope
                self.last_spoken_line = roast_line
                self.hud.set_speaking(True, roast_line)
                
                # Broadcast to web HUD
                broadcast({
                    "type": "speak",
                    "text": roast_line,
                    "envelope": envelope.tolist()
                })
                broadcast({"type": "playing", "value": True})
                
                self._log_event('roast', f"Played: {roast_line}")
            else:
                print(f"Failed to play roast: {roast_line}")
                
        except Exception as e:
            print(f"Failed to synthesize roast: {e}")
    
    def _add_jarvis_personality(self, base_line: str) -> str:
        """Add Jarvis-style personality and wit to roast lines."""
        import random
        
        # Jarvis-style suffixes that add personality
        jarvis_suffixes = [
            " *sigh*",
            " *rolls eyes*",
            " *chuckles*",
            " *sarcastic*",
            " *slow clap*",
            " *raises eyebrow*",
            " *unimpressed*",
            " *amused*",
            " *classic*",
            " *obviously*",
            " *naturally*",
            " *of course*",
            " *shocking*",
            " *surprising*",
            " *predictable*",
            " *inevitable*"
        ]
        
        # Jarvis-style prefixes for variety
        jarvis_prefixes = [
            "Heh, ",
            "Oh, ",
            "Well, ",
            "Ah, ",
            "Breaking news: ",
            "Update: ",
            "Alert: ",
            "Notice: ",
            "FYI: ",
            "Just saying: ",
            "For the record: ",
            "In case you were wondering: "
        ]
        
        # 30% chance to add a prefix
        if random.random() < 0.3:
            base_line = random.choice(jarvis_prefixes) + base_line
        
        # 40% chance to add a suffix
        if random.random() < 0.4:
            base_line = base_line + random.choice(jarvis_suffixes)
        
        # 20% chance to add both
        if random.random() < 0.2:
            base_line = random.choice(jarvis_prefixes) + base_line + random.choice(jarvis_suffixes)
        
        return base_line
    
    def _add_context_awareness(self, base_line: str, away_duration: float) -> str:
        """Add context-aware commentary based on how long user has been away."""
        import random
        
        # Context-aware additions based on away duration
        if away_duration >= 5.0:
            # Been away for a while - more dramatic
            dramatic_additions = [
                " I was beginning to think you'd abandoned the project entirely.",
                " At this rate, the code will be obsolete before you finish it.",
                " Your attention span is truly... impressive. In the worst way possible.",
                " I've seen glaciers move faster than your focus.",
                " This is getting concerning, sir. Should I call for help?"
            ]
            if random.random() < 0.6:  # 60% chance for dramatic addition
                base_line += random.choice(dramatic_additions)
        
        elif away_duration >= 3.0:
            # Medium away time - mildly sarcastic
            medium_additions = [
                " Classic you.",
                " As expected.",
                " How very... consistent.",
                " *sigh* Predictable.",
                " Another day, another distraction."
            ]
            if random.random() < 0.4:  # 40% chance for medium addition
                base_line += random.choice(medium_additions)
        
        elif away_duration >= 1.0:
            # Short away time - light teasing
            light_additions = [
                " Already?",
                " That was quick.",
                " Impressive speed.",
                " New record?",
                " Efficiently inefficient."
            ]
            if random.random() < 0.3:  # 30% chance for light addition
                base_line += random.choice(light_additions)
        
        return base_line
    
    def _handle_click(self, x: int, y: int):
        """Handle mouse click events."""
        print(f"🎯 Click detected at ({x}, {y})")
        print(f"📐 Camera width: {self.config['video']['cam_width']}, Total width: {self.config['video']['width']}")
        
        # Check if click is in HUD area
        if x > self.config['video']['cam_width'] and self.tts_manager:
            # Adjust x coordinate for HUD area
            hud_x = x - self.config['video']['cam_width']
            print(f"🎯 Adjusted HUD coordinates: ({hud_x}, {y})")
            
            # Check if click is on the orb
            if self.hud.hit_test_orb(hud_x, y):
                print("🎯 Orb clicked! Triggering TTS...")
                # Force speak the default line
                default_line = "You're not Iron Man lil bro"
                self.bubble.set_text(default_line)
                
                try:
                    audio, envelope, duration, sample_rate = self.tts_manager.synth(
                        default_line,
                        self.config['tts']['speaking_rate']
                    )
                    
                    if self.tts_manager.play(audio, sample_rate=sample_rate):
                        self.speaking_start_time = time.time()
                        self.current_envelope = envelope
                        self.last_spoken_line = default_line
                        self.hud.set_speaking(True, default_line)
                        self._log_event('click', f"Clicked bubble: {default_line}")
                        print(f"✅ TTS playing: {default_line}")
                    else:
                        print("❌ Failed to play clicked audio")
                        
                except Exception as e:
                    print(f"❌ Failed to synthesize clicked audio: {e}")
            else:
                print(f"❌ Click not within bubble bounds")
        else:
            if not self.tts_manager:
                print(f"❌ TTS manager not available")
            else:
                print(f"❌ Click not in bubble area (x={x} <= cam_width={self.config['video']['cam_width']})")
    
    def _handle_keyboard(self, key: int) -> bool:
        """Handle keyboard input. Returns True if should continue, False to quit."""
        if key == ord('q') or key == ord('Q'):
            return False
        elif key == ord(' '):
            active = self.focus_logic.toggle_active()
            status = "ACTIVE" if active else "INACTIVE"
            self._log_event('toggle', f"System toggled {status}")
            print(f"System toggled {status}")
        elif key == ord('r') or key == ord('R'):
            self.focus_logic.reset_cooldown()
            self.bubble.set_text("")
            self.hud.set_speaking(False)
            self.last_spoken_line = ""
            self._log_event('reset', "Cooldown reset")
            print("Cooldown reset")
        
        return True
    
    def run(self):
        """Main application loop."""
        print("🚀 Starting Jarvis Study Detection...")
        
        # Start WebSocket server
        start_ws_server_in_thread()
        
        # Register click handler for web HUD
        on_click(lambda: self._trigger_default_roast())
        
        # Initialize TTS
        if not self.initialize_tts():
            print("⚠️  Continuing without TTS functionality")
        else:
            # Set callback for TTS playback end
            self.tts_manager.set_playback_end_callback(self._on_tts_playback_end)
        
        # Initialize video capture
        if not self.start_video_capture():
            print("❌ Failed to start video capture")
            return
        
        # Create window
        window_name = "Jarvis Focus"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, self.config['video']['width'], self.config['video']['height'])
        
        # Set mouse callback
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                self._handle_click(x, y)
        
        cv2.setMouseCallback(window_name, mouse_callback)
        
        print("✅ Application started successfully!")
        print("   Controls: Space (toggle), R (reset), Q (quit)")
        print("   Click the bubble to force speak")
        
        self.running = True
        last_time = time.time()
        
        try:
            while self.running:
                # Read frame
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to read frame")
                    break
                
                # Process frame
                output_frame = self.process_frame(frame)
                
                # Broadcast status to web HUD
                current_status = self.focus_logic.get_status()
                broadcast({"type": "status", "value": current_status})
                
                # Update animations
                current_time = time.time()
                delta_time = current_time - last_time
                self.bubble.update_animation(delta_time)
                
                # Update bubble pulse from audio envelope
                if (self.tts_manager and 
                    hasattr(self.tts_manager, 'is_playing') and 
                    self.tts_manager.is_playing and 
                    self.current_envelope is not None):
                    # Get current envelope value based on playback progress
                    progress = (current_time - self.speaking_start_time) / 2.0  # Approximate duration
                    if 0 <= progress <= 1:
                        envelope_index = int(progress * len(self.current_envelope))
                        if envelope_index < len(self.current_envelope):
                            self.bubble.set_pulse_intensity(self.current_envelope[envelope_index])
                
                # Display frame
                cv2.imshow(window_name, output_frame)
                
                # Handle input
                key = cv2.waitKey(1) & 0xFF
                if key != 255:
                    if not self._handle_keyboard(key):
                        break
                
                last_time = current_time
                
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        print("🧹 Cleaning up...")
        
        if self.tts_manager:
            self.tts_manager.cleanup()
        
        if self.cap:
            self.cap.release()
        
        cv2.destroyAllWindows()
        
        self._log_event('quit', 'Application closed')
        print("✅ Cleanup complete")
    
    def _on_tts_playback_end(self):
        """Called when TTS playback ends."""
        self.hud.set_speaking(False)
        # Broadcast to web HUD
        broadcast({"type": "playing", "value": False})
    
    def _trigger_default_roast(self):
        """Trigger the default roast line from web HUD click."""
        if not self.tts_manager:
            return
            
        default_line = "You're not Iron-Man lil bro"
        print(f"🎯 Web HUD triggered default roast: {default_line}")
        
        try:
            audio, envelope, duration, sample_rate = self.tts_manager.synth(
                default_line,
                self.config['tts']['speaking_rate']
            )
            
            if self.tts_manager.play(audio, sample_rate=sample_rate):
                self.speaking_start_time = time.time()
                self.current_envelope = envelope
                self.last_spoken_line = default_line
                self.hud.set_speaking(True, default_line)
                
                # Broadcast to web HUD
                broadcast({
                    "type": "speak",
                    "text": default_line,
                    "envelope": envelope.tolist()
                })
                broadcast({"type": "playing", "value": True})
                
                self._log_event('web_click', f"Web HUD triggered: {default_line}")
            else:
                print("❌ Failed to play default roast")
                
        except Exception as e:
            print(f"❌ Failed to synthesize default roast: {e}")

def main():
    """Main entry point."""
    app = JarvisApp()
    app.run()

if __name__ == "__main__":
    main()
