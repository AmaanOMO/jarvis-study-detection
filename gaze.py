import cv2
import mediapipe as mp
import numpy as np
from typing import Tuple, Dict, Any

class GazeDetector:
    def __init__(self):
        """Initialize MediaPipe Face Mesh for gaze detection."""
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            refine_landmarks=True,
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Smoothing for detection stability
        self.status_history = []
        self.history_size = 5  # Keep last 5 frames
        self.confidence_threshold = 0.6  # Need 60% of frames to agree
        
        # Landmark indices for key facial features
        self.LANDMARKS = {
            'nose': 1,
            'left_eye_inner': 133,
            'left_eye_outer': 33,
            'left_iris': 468,
            'right_eye_inner': 362,
            'right_eye_outer': 263,
            'right_iris': 473,
            'left_mouth': 61,
            'right_mouth': 291,
            'chin': 152
        }
        
        # 3D model points for pose estimation (adjusted for better calibration)
        self.model_points = np.array([
            [0.0, 0.0, 0.0],           # nose
            [-25.0, -8.0, -25.0],      # left eye inner
            [25.0, -8.0, -25.0],       # right eye inner
            [-25.0, 8.0, -25.0],       # left eye outer
            [25.0, 8.0, -25.0],        # right eye outer
            [-25.0, -25.0, -25.0],     # left mouth
            [25.0, -25.0, -25.0],      # right mouth
            [0.0, -40.0, -25.0]        # chin
        ], dtype=np.float64)
        
        # Camera matrix (approximate for webcam)
        self.camera_matrix = np.array([
            [1000, 0, 640],
            [0, 1000, 480],
            [0, 0, 1]
        ], dtype=np.float64)
        
        self.dist_coeffs = np.zeros((4, 1))
    
    def detect(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Detect gaze direction and head pose from frame.
        
        Returns:
            Dict with keys: status, yaw, pitch, gaze_ratio
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            return {
                'status': 'AWAY',
                'yaw': 0.0,
                'pitch': 0.0,
                'gaze_ratio': 0.5
            }
        
        landmarks = results.multi_face_landmarks[0]
        h, w = frame.shape[:2]
        
        # Extract 2D points for pose estimation
        image_points = np.array([
            [landmarks.landmark[self.LANDMARKS['nose']].x * w, 
             landmarks.landmark[self.LANDMARKS['nose']].y * h],
            [landmarks.landmark[self.LANDMARKS['left_eye_inner']].x * w,
             landmarks.landmark[self.LANDMARKS['left_eye_inner']].y * h],
            [landmarks.landmark[self.LANDMARKS['right_eye_inner']].x * w,
             landmarks.landmark[self.LANDMARKS['right_eye_inner']].y * h],
            [landmarks.landmark[self.LANDMARKS['left_eye_outer']].x * w,
             landmarks.landmark[self.LANDMARKS['left_eye_outer']].y * h],
            [landmarks.landmark[self.LANDMARKS['right_eye_outer']].x * w,
             landmarks.landmark[self.LANDMARKS['right_eye_outer']].y * h],
            [landmarks.landmark[self.LANDMARKS['left_mouth']].x * w,
             landmarks.landmark[self.LANDMARKS['left_mouth']].y * h],
            [landmarks.landmark[self.LANDMARKS['right_mouth']].x * w,
             landmarks.landmark[self.LANDMARKS['right_mouth']].y * h],
            [landmarks.landmark[self.LANDMARKS['chin']].x * w,
             landmarks.landmark[self.LANDMARKS['chin']].y * h]
        ], dtype=np.float64)
        
        # Solve PnP for pose estimation
        try:
            _, rvec, _ = cv2.solvePnP(
                self.model_points, image_points, 
                self.camera_matrix, self.dist_coeffs
            )
            
            # Convert rotation vector to Euler angles
            rmat, _ = cv2.Rodrigues(rvec)
            yaw = np.arctan2(rmat[2, 0], rmat[2, 2]) * 180 / np.pi
            pitch = np.arcsin(-rmat[2, 1]) * 180 / np.pi
            
            # Apply correction factor for better calibration
            yaw = yaw * 0.6  # Reduce extreme values
            pitch = pitch * 0.8  # Reduce extreme values
            
        except:
            yaw, pitch = 0.0, 0.0
        
        # Calculate gaze ratio for both eyes
        left_iris_x = landmarks.landmark[self.LANDMARKS['left_iris']].x * w
        left_inner_x = landmarks.landmark[self.LANDMARKS['left_eye_inner']].x * w
        left_outer_x = landmarks.landmark[self.LANDMARKS['left_eye_outer']].x * w
        
        right_iris_x = landmarks.landmark[self.LANDMARKS['right_iris']].x * w
        right_inner_x = landmarks.landmark[self.LANDMARKS['right_eye_inner']].x * w
        right_outer_x = landmarks.landmark[self.LANDMARKS['right_eye_outer']].x * w
        
        # Calculate horizontal gaze ratios
        left_ratio = (left_iris_x - left_inner_x) / (left_outer_x - left_inner_x) if left_outer_x != left_inner_x else 0.5
        right_ratio = (right_iris_x - right_inner_x) / (right_outer_x - right_inner_x) if right_outer_x != right_inner_x else 0.5
        
        # Average gaze ratio
        gaze_ratio = (left_ratio + right_ratio) / 2
        
        # Determine status based on thresholds
        raw_status = self._determine_status(yaw, pitch, gaze_ratio)
        
        # Apply smoothing to prevent flickering
        status = self._apply_smoothing(raw_status)
        
        # Debug logging
        if hasattr(self, 'debug_counter'):
            self.debug_counter += 1
        else:
            self.debug_counter = 0
            
        if self.debug_counter % 30 == 0:  # Log every 30 frames (about 1 second)
            print(f"DEBUG: Yaw={yaw:.1f}°, Pitch={pitch:.1f}°, Gaze={gaze_ratio:.2f}, Raw={raw_status}, Smoothed={status}")
            print(f"DEBUG: Thresholds - Yaw<{getattr(self, 'yaw_threshold', 35.0)}, Pitch<{getattr(self, 'pitch_threshold', 25.0)}, Gaze[{getattr(self, 'gaze_min', 0.25):.2f}-{getattr(self, 'gaze_max', 0.75):.2f}]")
        
        return {
            'status': status,
            'yaw': yaw,
            'pitch': pitch,
            'gaze_ratio': gaze_ratio
        }
    
    def _determine_status(self, yaw: float, pitch: float, gaze_ratio: float) -> str:
        """Determine if user is looking at screen based on thresholds."""
        # Use updated thresholds from config
        yaw_threshold = getattr(self, 'yaw_threshold', 35.0)
        pitch_threshold = getattr(self, 'pitch_threshold', 25.0)
        gaze_min = getattr(self, 'gaze_min', 0.25)
        gaze_max = getattr(self, 'gaze_max', 0.75)
        
        # Primary detection using pose + gaze
        if (abs(yaw) < yaw_threshold and 
            abs(pitch) < pitch_threshold and 
            gaze_min <= gaze_ratio <= gaze_max):
            return 'LOOKING'
        
        # Fallback: if pose estimation seems wrong (extreme values), use only gaze
        if abs(yaw) > 90.0 or abs(pitch) > 90.0:
            # Pose estimation failed, use gaze ratio only
            if gaze_min <= gaze_ratio <= gaze_max:
                return 'LOOKING'
            else:
                return 'AWAY'
        
        return 'AWAY'
    
    def update_thresholds(self, yaw_deg: float, pitch_deg: float, 
                         gaze_center_min: float, gaze_center_max: float):
        """Update detection thresholds from config."""
        self.yaw_threshold = yaw_deg
        self.pitch_threshold = pitch_deg
        self.gaze_min = gaze_center_min
        self.gaze_max = gaze_center_max
    
    def _apply_smoothing(self, current_status: str) -> str:
        """Apply smoothing to prevent status flickering."""
        # Add current status to history
        self.status_history.append(current_status)
        
        # Keep only the last N frames
        if len(self.status_history) > self.history_size:
            self.status_history.pop(0)
        
        # If we don't have enough history yet, return current status
        if len(self.status_history) < self.history_size:
            return current_status
        
        # Count occurrences of each status
        looking_count = self.status_history.count('LOOKING')
        away_count = self.status_history.count('AWAY')
        
        # Calculate confidence
        total_frames = len(self.status_history)
        looking_confidence = looking_count / total_frames
        away_confidence = away_count / total_frames
        
        # Return status with highest confidence above threshold
        if looking_confidence >= self.confidence_threshold:
            return 'LOOKING'
        elif away_confidence >= self.confidence_threshold:
            return 'AWAY'
        else:
            # If no clear winner, maintain previous status
            return self.status_history[-2] if len(self.status_history) > 1 else current_status
    
    def __del__(self):
        """Clean up MediaPipe resources."""
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()
