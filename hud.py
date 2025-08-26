import cv2
import numpy as np
import time
import math
from typing import Tuple, List

class JarvisHUD:
    def __init__(self, width: int, height: int, config: dict):
        """
        Initialize Jarvis HUD with cinematic sci-fi aesthetic.
        
        Args:
            width: Canvas width
            height: Canvas height
            config: Configuration dictionary
        """
        self.width = width
        self.height = height
        self.config = config
        
        # Animation state
        self.t = 0.0  # Time accumulator
        self.type_i = 0  # Typewriter character index
        self.is_speaking = False
        self.typewriter_start_time = 0.0
        self.current_line = ""
        self.target_line = ""
        
        # Precompute particle positions for performance
        self.particles = self._generate_particles(50)  # 50 floating particles
        
        # HUD configuration
        self.hud_config = config.get('hud', {})
        self.layout = self.hud_config.get('layout', 'full')
        self.orb_base_radius = self.hud_config.get('orb_base_radius', 110)
        self.sweep_count = self.hud_config.get('sweep_count', 8)
        self.ring_offsets = self.hud_config.get('ring_offsets', [-40, 0, 30])
        self.typewriter_cps = self.hud_config.get('typewriter_cps', 40)
        
        # Colors (BGR format)
        self.colors = {
            'bg': (20, 15, 11),           # Deep navy #0b0f14
            'primary': (255, 170, 90),     # Bright blue #5AB4FF
            'accent': (200, 140, 70),      # Medium blue
            'muted': (120, 100, 70),       # Dark blue
            'text': (255, 255, 255),       # White text
            'status_good': (90, 255, 90),  # Green for LOOKING
            'status_bad': (90, 90, 255)    # Red for AWAY
        }
        
        # Center coordinates
        if self.layout == 'full':
            self.center_x = width // 2
            self.center_y = height // 2
        else:
            # For split mode, center in right panel
            self.center_x = width // 2
            self.center_y = height // 2
    
    def _generate_particles(self, count: int) -> List[Tuple[float, float, float, float]]:
        """Generate random particle positions with phases and speeds."""
        particles = []
        for _ in range(count):
            x = np.random.uniform(0, self.width)
            y = np.random.uniform(0, self.height)
            phase = np.random.uniform(0, 2 * np.pi)
            speed = np.random.uniform(0.5, 2.0)
            particles.append((x, y, phase, speed))
        return particles
    
    def set_speaking(self, speaking: bool, line: str = None):
        """Start/stop typewriter animation for a line."""
        self.is_speaking = speaking
        if speaking and line:
            self.target_line = line
            self.current_line = ""
            self.typewriter_start_time = time.time()
            self.type_i = 0
    
    def hit_test_orb(self, x: int, y: int) -> bool:
        """Return True if (x,y) is inside orb click radius."""
        distance = math.sqrt((x - self.center_x) ** 2 + (y - self.center_y) ** 2)
        return distance <= self.orb_base_radius
    
    def _draw_glow_orb(self, canvas: np.ndarray, pulse: float, scale: float):
        """Draw the central glowing orb with layered effects."""
        # Pulse scale
        pulse_scale = 1.0 + 0.05 * pulse
        
        # Base orb
        base_radius = int(self.orb_base_radius * scale * pulse_scale)
        cv2.circle(canvas, (self.center_x, self.center_y), base_radius, self.colors['primary'], -1)
        
        # Inner glow (brighter core)
        inner_radius = int(base_radius * 0.7)
        cv2.circle(canvas, (self.center_x, self.center_y), inner_radius, self.colors['accent'], -1)
        
        # Outer halo (soft glow)
        outer_radius = int(base_radius * 1.3)
        halo_color = (*self.colors['primary'], 100)  # Semi-transparent
        cv2.circle(canvas, (self.center_x, self.center_y), outer_radius, self.colors['muted'], 2)
        
        # Apply Gaussian blur for glow effect
        blurred = cv2.GaussianBlur(canvas, (21, 21), 0)
        canvas[:] = cv2.addWeighted(canvas, 0.7, blurred, 0.3, 0)
    
    def _draw_concentric_rings(self, canvas: np.ndarray, scale: float):
        """Draw concentric rings around the orb."""
        for offset in self.ring_offsets:
            radius = int((self.orb_base_radius + offset) * scale)
            # Semi-transparent rings
            ring_color = (*self.colors['accent'], 150)
            cv2.circle(canvas, (self.center_x, self.center_y), radius, self.colors['accent'], 2)
    
    def _draw_sweep_lines(self, canvas: np.ndarray, scale: float):
        """Draw rotating sweep lines emanating from center."""
        sweep_radius = int((self.orb_base_radius + 70) * scale)
        rotation_speed = 0.6
        
        for i in range(self.sweep_count):
            angle = self.t * rotation_speed + (i * 2 * np.pi / self.sweep_count)
            end_x = int(self.center_x + sweep_radius * math.cos(angle))
            end_y = int(self.center_y + sweep_radius * math.sin(angle))
            
            # Draw sweep line
            cv2.line(canvas, (self.center_x, self.center_y), (end_x, end_y), 
                     self.colors['primary'], 2)
    
    def _draw_particles(self, canvas: np.ndarray):
        """Draw floating particles with parallax effect."""
        for x, y, phase, speed in self.particles:
            # Animate particle position
            animated_x = int(x + math.sin(self.t * speed + phase) * 10)
            animated_y = int(y + math.cos(self.t * speed + phase) * 5)
            
            # Draw small glowing particle
            cv2.circle(canvas, (animated_x, animated_y), 1, self.colors['primary'], -1)
    
    def _draw_header_text(self, canvas: np.ndarray):
        """Draw JARVIS and Online labels."""
        # Top-left: ● JARVIS
        cv2.circle(canvas, (30, 30), 6, self.colors['primary'], -1)
        cv2.putText(canvas, "JARVIS", (45, 35), cv2.FONT_HERSHEY_DUPLEX, 1.0, 
                    self.colors['text'], 2)
        
        # Top-right: ● Online
        cv2.circle(canvas, (self.width - 80, 30), 6, self.colors['primary'], -1)
        cv2.putText(canvas, "Online", (self.width - 70, 35), cv2.FONT_HERSHEY_DUPLEX, 0.8, 
                    self.colors['text'], 2)
    
    def _draw_status_text(self, canvas: np.ndarray, status_text: str):
        """Draw status microtext near the orb."""
        # Status text below orb
        status_y = self.center_y + self.orb_base_radius + 40
        status_color = self.colors['status_good'] if status_text == 'LOOKING' else self.colors['status_bad']
        
        cv2.putText(canvas, f"SYS.STATUS: {status_text}", 
                    (self.center_x - 80, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
                    status_color, 1)
    
    def _draw_typewriter_text(self, canvas: np.ndarray):
        """Draw typewriter text under the orb."""
        if not self.target_line:
            return
        
        # Update typewriter animation
        if self.is_speaking:
            elapsed = time.time() - self.typewriter_start_time
            target_chars = int(elapsed * self.typewriter_cps / 1000.0)
            self.current_line = self.target_line[:target_chars]
        
        if self.current_line:
            # Draw typewriter text
            text_y = self.center_y + self.orb_base_radius + 80
            cv2.putText(canvas, self.current_line, 
                        (self.center_x - 150, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, 
                        self.colors['text'], 2)
    
    def draw(self, canvas: np.ndarray, status_text: str, last_line: str, pulse: float, dt: float) -> np.ndarray:
        """
        Draw HUD onto provided BGR canvas and return it.
        
        Args:
            canvas: BGR canvas to draw on
            status_text: "LOOKING" or "AWAY"
            last_line: most recent spoken line
            pulse: 0..1 from audio envelope
            dt: seconds since last frame
        """
        # Update time
        self.t += dt
        
        # Fill background
        canvas[:] = self.colors['bg']
        
        # Draw floating particles
        self._draw_particles(canvas)
        
        # Compute pulse scale
        scale = 1.0 + 0.05 * pulse
        
        # Draw concentric rings
        self._draw_concentric_rings(canvas, scale)
        
        # Draw sweep lines
        self._draw_sweep_lines(canvas, scale)
        
        # Draw central glowing orb
        self._draw_glow_orb(canvas, pulse, scale)
        
        # Draw header text
        self._draw_header_text(canvas)
        
        # Draw status text
        self._draw_status_text(canvas, status_text)
        
        # Draw typewriter text
        self._draw_typewriter_text(canvas)
        
        return canvas
