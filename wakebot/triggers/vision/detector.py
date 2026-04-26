"""
WakeBot Vision Detector
Detects human presence/faces using OpenCV Haar Cascades.
"""

import cv2
import time
from typing import Optional, Any
from wakebot.core.detector import BaseDetector
from wakebot.core.logger import WakeBotLogger


class PersonDetector(BaseDetector):
    """Detects human presence in video frames"""
    
    def __init__(self, min_face_width: int = 30):
        """
        Initialize PersonDetector
        """
        self.logger = WakeBotLogger()
        self.min_face_width = min_face_width
        
        # Load Haar Cascades
        cascade_path_front = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        cascade_path_profile = cv2.data.haarcascades + 'haarcascade_profileface.xml'
        
        self.face_cascade = cv2.CascadeClassifier(cascade_path_front)
        self.face_cascade_profile = cv2.CascadeClassifier(cascade_path_profile)
        
        self.person_detected = False
        self.is_active = False
        
    def process(self, frame: Any) -> Optional[str]:
        """Process a video frame and detect persons"""
        if frame is None:
            return None
            
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces from multiple angles
            faces_front = self.face_cascade.detectMultiScale(
                gray, 1.05, 4, minSize=(self.min_face_width, self.min_face_width)
            )
            
            faces_profile = self.face_cascade_profile.detectMultiScale(
                gray, 1.05, 5, minSize=(self.min_face_width, self.min_face_width)
            )
            
            found = len(faces_front) > 0 or len(faces_profile) > 0
            
            if found:
                if not self.person_detected:
                    self.person_detected = True
                    self.logger.info("Person detected via camera")
                    return "PERSON_DETECTED"
            else:
                self.person_detected = False
                
            return None
        except Exception as e:
            self.logger.error(f"Error in vision detection: {e}")
            return None

    def start(self):
        """Start the detector"""
        self.is_active = True

    def stop(self):
        """Stop the detector"""
        self.is_active = False

    def check_and_reset(self) -> bool:
        """Vision detector is usually processed synchronously in a loop"""
        return False
