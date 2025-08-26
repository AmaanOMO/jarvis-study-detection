import cv2
import numpy as np
import time
from typing import Tuple, Optional

class VoiceBubble:
    def __init__(self, width: int, height: int):
        """
        Initialize voice bubble UI.
        
        Args:
            width: Width of bubble area
            height: Height of bubble area
        """
        self.width = width
        self.height = height
        
        # Animation state
        self.pulse_value = 0.0
        self.pulse_direction = 1
        self.pulse_speed = 2.0
        
        # Text animation
        self.current_text = ""
        self.target_text = ""
        self.typewriter_start_time = 0
        self.typewriter_speed = 40  # characters per second
        
        # Colors (high contrast for filming)
        self.colors = {
            'background': (20, 20, 20),      # Dark gray
            'bubble': (60, 60, 60),          # Medium gray
            'bubble_highlight': (100, 100, 100),  # Light gray
            'text': (255, 255, 255),         # White
            'accent': (0, 255, 255),         # Cyan
            'status_good': (0, 255, 0),      # Green
            'status_bad': (0, 0, 255)        # Red
        }
        
        # Bubble dimensions and position
        self.bubble_radius = min(width, height) // 4
        self.bubble_center = (width // 2, height // 2)
        
        # Click detection
        self.clickable_rect = (
            self.bubble_center[0] - self.bubble_radius,
            self.bubble_center[1] - self.bubble_radius,
            self.bubble_center[0] + self.bubble_radius,
            self.bubble_center[1] + self.bubble_radius
        )
    
    def update_animation(self, delta_time: float):
        """Update animation state."""
        # Update pulse animation
        self.pulse_value += self.pulse_direction * self.pulse_speed * delta_time
        
        if self.pulse_value >= 1.0:
            self.pulse_value = 1.0
            self.pulse_direction = -1
        elif self.pulse_value <= 0.0:
            self.pulse_value = 0.0
            self.pulse_direction = 1
        
        # Update typewriter effect
        if self.target_text and self.current_text != self.target_text:
            elapsed = time.time() - self.typewriter_start_time
            target_chars = int(elapsed * self.typewriter_speed)
            self.current_text = self.target_text[:target_chars]
    
    def set_text(self, text: str):
        """Set new text to display with typewriter effect."""
        self.target_text = text
        self.current_text = ""
        self.typewriter_start_time = time.time()
    
    def set_pulse_intensity(self, intensity: float):
        """Set pulse intensity from audio envelope (0.0 to 1.0)."""
        self.pulse_value = max(0.0, min(1.0, intensity))
    
    def draw(self, canvas: np.ndarray, speaking: bool = False) -> np.ndarray:
        """
        Draw the voice bubble on the canvas.
        
        Args:
            canvas: Canvas to draw on
            speaking: Whether currently speaking
            
        Returns:
            Canvas with bubble drawn
        """
        # Create a copy of the canvas
        result = canvas.copy()
        
        # Draw background
        cv2.rectangle(result, (0, 0), (self.width, self.height), 
                     self.colors['background'], -1)
        
        # Calculate bubble position with pulse animation
        pulse_offset = int(self.pulse_value * 10)  # 0-10 pixel offset
        bubble_center = (
            self.bubble_center[0] + pulse_offset,
            self.bubble_center[1] + pulse_offset
        )
        
        # Draw main bubble
        bubble_color = self.colors['bubble_highlight'] if speaking else self.colors['bubble']
        cv2.circle(result, bubble_center, self.bubble_radius, bubble_color, -1)
        
        # Draw bubble outline
        cv2.circle(result, bubble_center, self.bubble_radius, self.colors['accent'], 3)
        
        # Draw title
        title = "JARVIS"
        title_font = cv2.FONT_HERSHEY_DUPLEX
        title_scale = 1.2
        title_thickness = 2
        title_size = cv2.getTextSize(title, title_font, title_scale, title_thickness)[0]
        title_x = bubble_center[0] - title_size[0] // 2
        title_y = bubble_center[1] - title_size[1] - 20
        
        cv2.putText(result, title, (title_x, title_y), title_font, title_scale,
                    self.colors['text'], title_thickness)
        
        # Draw current text with typewriter effect
        if self.current_text:
            # Split text into lines for better display
            words = self.current_text.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                text_size = cv2.getTextSize(test_line, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                
                if text_size[0] > self.width - 40:  # Leave margin
                    if current_line:
                        lines.append(current_line)
                        current_line = word
                    else:
                        lines.append(word)
                else:
                    current_line = test_line
            
            if current_line:
                lines.append(current_line)
            
            # Draw lines
            line_height = 30
            start_y = bubble_center[1] + 20
            
            for i, line in enumerate(lines):
                if i >= 3:  # Limit to 3 lines
                    break
                
                line_size = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                line_x = bubble_center[0] - line_size[0] // 2
                line_y = start_y + i * line_height
                
                cv2.putText(result, line, (line_x, line_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            self.colors['text'], 2)
        
        # Draw speaking indicator
        if speaking:
            # Animated dots
            dot_radius = 4
            dot_spacing = 20
            center_x = bubble_center[0]
            center_y = bubble_center[1] + self.bubble_radius + 30
            
            for i in range(3):
                dot_x = center_x + (i - 1) * dot_spacing
                dot_y = center_y + int(np.sin(time.time() * 3 + i) * 5)
                cv2.circle(result, (dot_x, dot_y), dot_radius, self.colors['accent'], -1)
        
        return result
    
    def is_clicked(self, x: int, y: int) -> bool:
        """
        Check if a point is within the clickable bubble area.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if point is within clickable area
        """
        # Calculate current bubble center with pulse animation
        pulse_offset = int(self.pulse_value * 10)
        current_center_x = self.bubble_center[0] + pulse_offset
        current_center_y = self.bubble_center[1] + pulse_offset
        
        # Check if point is within current bubble radius
        distance = ((x - current_center_x) ** 2 + (y - current_center_y) ** 2) ** 0.5
        return distance <= self.bubble_radius
    
    def get_clickable_area(self) -> Tuple[int, int, int, int]:
        """Get the clickable rectangle area (x1, y1, x2, y2)."""
        return self.clickable_rect
    
    def draw_debug_info(self, canvas: np.ndarray, status: str, away_duration: float = 0.0):
        """Draw debug information on the canvas."""
        # Status text
        status_color = self.colors['status_good'] if status == 'LOOKING' else self.colors['status_bad']
        status_text = f"Status: {status}"
        cv2.putText(canvas, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    status_color, 2)
        
        # Away duration
        if away_duration > 0:
            duration_text = f"Away: {away_duration:.1f}s"
            cv2.putText(canvas, duration_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        self.colors['accent'], 2)
        
        # Controls hint
        controls_text = "Space: Toggle | R: Reset | Q: Quit"
        cv2.putText(canvas, controls_text, (10, self.height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    self.colors['text'], 1)
