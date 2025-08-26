import cv2
import numpy as np
import time
from typing import Tuple, Optional

class JarvisHUD:
    def __init__(self, width: int, height: int, config: dict):
        """
        Initialize Jarvis HUD with cinematic visual effects.
        
        Args:
            width: Canvas width
            height: Canvas height
            config: Configuration dictionary
        """
        self.width = width
        self.height = height
        self.config = config
        
        # HUD configuration with defaults
        hud_config = config.get('hud', {})
        self.layout = hud_config.get('layout', 'full')
        self.orb_base_radius = hud_config.get('orb_base_radius', 110)
        self.sweep_count = hud_config.get('sweep_count', 8)
        self.ring_offsets = hud_config.get('ring_offsets', [-40, 0, 30])
        self.typewriter_cps = hud_config.get('typewriter_cps', 40)
        
        # Colors (BGR format for OpenCV)
        self.colors = {
            'bg': (11, 15, 20),           # Deep navy #0b0f14
            'primary': (255, 170, 90),     # Bright blue #5AB4FF
            'accent': (200, 140, 70),      # Medium blue
            'muted': (120, 100, 70),       # Dark blue
            'text': (255, 255, 255),       # White
            'glow': (180, 120, 60)         # Soft blue glow
        }
        
        # Animation state
        self.t = 0.0  # Time accumulator
        self.type_i = 0  # Typewriter character index
        self.is_speaking = False
        self.speaking_start_time = 0.0
        self.current_line = ""
        self.target_line = ""
        
        # Precompute particle positions for starfield effect
        self.particles = self._generate_particles(50)
        
        # Orb center (will be set based on layout)
        self.orb_center = (width // 2, height // 2)
    
    def _generate_particles(self, count: int) -> list:
        """Generate random particle positions for starfield effect."""
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
            self.type_i = 0
            self.speaking_start_time = time.time()
        elif not speaking:
            self.current_line = self.target_line
    
    def hit_test_orb(self, x: int, y: int) -> bool:
        """Return True if (x,y) is inside orb click radius."""
        dx = x - self.orb_center[0]
        dy = y - self.orb_center[1]
        distance = (dx * dx + dy * dy) ** 0.5
        return distance <= self.orb_base_radius
    
    def _draw_orb(self, canvas: np.ndarray, pulse: float):
        """Draw the central glowing orb with pulse animation."""
        # Pulse scale
        scale = 1.0 + 0.1 * pulse
        
        # Draw multiple layers for glow effect
        for i in range(5):
            radius = int(self.orb_base_radius * scale * (0.3 + 0.7 * i / 4))
            alpha = 0.1 + 0.2 * (1 - i / 4)
            
            # Create a temporary canvas for this layer
            temp_canvas = canvas.copy()
            
            # Draw the circle
            cv2.circle(temp_canvas, self.orb_center, radius, self.colors['primary'], -1)
            
            # Apply alpha blending
            canvas = cv2.addWeighted(canvas, 1 - alpha, temp_canvas, alpha, 0)
        
        # Draw the core orb
        core_radius = int(self.orb_base_radius * scale * 0.3)
        cv2.circle(canvas, self.orb_center, core_radius, self.colors['text'], -1)
        
        # Add inner highlight
        highlight_radius = int(core_radius * 0.6)
        highlight_offset = (int(core_radius * 0.3), int(core_radius * 0.3))
        highlight_pos = (self.orb_center[0] - highlight_offset[0], 
                        self.orb_center[1] - highlight_offset[1])
        cv2.circle(canvas, highlight_pos, highlight_radius, (255, 255, 255), -1)
    
    def _draw_rings(self, canvas: np.ndarray):
        """Draw concentric rings around the orb."""
        for offset in self.ring_offsets:
            radius = self.orb_base_radius + offset
            # Draw ring with transparency
            cv2.circle(canvas, self.orb_center, radius, self.colors['accent'], 2)
            # Draw inner glow
            cv2.circle(canvas, self.orb_center, radius - 1, self.colors['muted'], 1)
    
    def _draw_sweep_lines(self, canvas: np.ndarray):
        """Draw rotating sweep lines emanating from the orb."""
        sweep_radius = self.orb_base_radius + 70
        
        for i in range(self.sweep_count):
            angle = self.t * 0.6 + (2 * np.pi * i / self.sweep_count)
            
            # Calculate end point
            end_x = int(self.orb_center[0] + sweep_radius * np.cos(angle))
            end_y = int(self.orb_center[1] + sweep_radius * np.sin(angle))
            
            # Draw the sweep line
            cv2.line(canvas, self.orb_center, (end_x, end_y), 
                    self.colors['primary'], 2)
            
            # Add glow effect
            cv2.line(canvas, self.orb_center, (end_x, end_y), 
                    self.colors['glow'], 1)
    
    def _draw_particles(self, canvas: np.ndarray):
        """Draw floating particles with parallax effect."""
        for x, y, phase, speed in self.particles:
            # Animate particle position
            animated_x = (x + self.t * speed * 10) % self.width
            animated_y = (y + np.sin(self.t * 0.5 + phase) * 5) % self.height
            
            # Draw particle
            cv2.circle(canvas, (int(animated_x), int(animated_y)), 1, 
                      self.colors['muted'], -1)
    
    def _draw_header_texts(self, canvas: np.ndarray):
        """Draw JARVIS and Online labels."""
        # Top-left: JARVIS
        cv2.circle(canvas, (30, 30), 6, self.colors['primary'], -1)
        cv2.putText(canvas, "JARVIS", (45, 35), cv2.FONT_HERSHEY_DUPLEX, 
                    0.8, self.colors['text'], 2)
        
        # Top-right: Online
        cv2.circle(canvas, (self.width - 30, 30), 6, self.colors['primary'], -1)
        cv2.putText(canvas, "Online", (self.width - 80, 35), cv2.FONT_HERSHEY_DUPLEX, 
                    0.8, self.colors['text'], 2)
    
    def _draw_status_text(self, canvas: np.ndarray, status_text: str):
        """Draw status microtext near the orb."""
        # System status
        status_pos = (self.orb_center[0] - 80, self.orb_center[1] + self.orb_base_radius + 40)
        cv2.putText(canvas, f"SYS.STATUS: {status_text}", status_pos, 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['accent'], 1)
        
        # Scan status
        scan_pos = (self.orb_center[0] - 80, self.orb_center[1] + self.orb_base_radius + 60)
        cv2.putText(canvas, "SCAN: ACTIVE [10.4.3]", scan_pos, 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['accent'], 1)
    
    def _draw_typewriter_text(self, canvas: np.ndarray):
        """Draw typewriter text under the orb."""
        if not self.target_line:
            return
        
        # Update typewriter animation
        if self.is_speaking:
            elapsed = time.time() - self.speaking_start_time
            target_chars = int(elapsed * self.typewriter_cps)
            self.current_line = self.target_line[:target_chars]
        
        if self.current_line:
            # Calculate text position (centered under orb)
            text_size = cv2.getTextSize(self.current_line, cv2.FONT_HERSHEY_SIMPLEX, 
                                       0.7, 2)[0]
            text_x = self.orb_center[0] - text_size[0] // 2
            text_y = self.orb_center[1] + self.orb_base_radius + 100
            
            # Draw text with glow effect
            cv2.putText(canvas, self.current_line, (text_x, text_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.colors['glow'], 3)
            cv2.putText(canvas, self.current_line, (text_x, text_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.colors['text'], 2)
    
    def draw(self, canvas: np.ndarray, status_text: str, last_line: str, 
             pulse: float, dt: float) -> np.ndarray:
        """
        Draw HUD onto provided BGR canvas and return it.
        
        Args:
            canvas: BGR canvas to draw on
            status_text: "LOOKING" or "AWAY"
            last_line: most recent spoken line
            pulse: 0..1 (from audio envelope)
            dt: seconds since last frame
            
        Returns:
            Canvas with HUD drawn
        """
        # Update animation time
        self.t += dt
        
        # Update target line if provided
        if last_line and last_line != self.target_line:
            self.target_line = last_line
        
        # Fill background
        canvas[:] = self.colors['bg']
        
        # Draw starfield particles
        self._draw_particles(canvas)
        
        # Draw HUD elements
        self._draw_orb(canvas, pulse)
        self._draw_rings(canvas)
        self._draw_sweep_lines(canvas)
        self._draw_header_texts(canvas)
        self._draw_status_text(canvas, status_text)
        self._draw_typewriter_text(canvas)
        
        return canvas
