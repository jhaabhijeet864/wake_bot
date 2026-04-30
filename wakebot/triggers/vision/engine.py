"""
WakeBot Vision Engine
Handles camera initialization and frame capture.
"""

import cv2
from typing import Optional


class CameraEngine:
    """Handles camera hardware lifecycle"""
    
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.camera: Optional[cv2.VideoCapture] = None
        
    def initialize(self) -> bool:
        """Initialize the camera"""
        try:
            self.camera = cv2.VideoCapture(self.camera_index)
            if not self.camera.isOpened():
                return False
            
            # Set optimal properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            return True
        except Exception as e:
            print(f"Error initializing camera: {e}")
            return False

    def is_opened(self) -> bool:
        """Check if camera is initialized and open."""
        return self.camera is not None and self.camera.isOpened()
            
    def read_frame(self):
        """Read a single frame from the camera"""
        if self.camera is None:
            return False, None
        return self.camera.read()
        
    def release(self):
        """Release camera resources"""
        if self.camera is not None:
            self.camera.release()
            self.camera = None
