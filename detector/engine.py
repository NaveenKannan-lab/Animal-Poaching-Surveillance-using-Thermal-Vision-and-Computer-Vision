import cv2
import time
import numpy as np
from ultralytics import YOLO

HUMAN_CLASS = 0
# COCO animal classes: bird, cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe
ANIMAL_CLASSES = {14, 15, 16, 17, 18, 19, 20, 21, 22, 23}

class DetectionEngine:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.confidence = 0.35  # Default confidence for humans
        self.animal_confidence = 0.15  # Lower confidence for animals in thermal
        self.sound_enabled = True  # Sound toggle

    def preprocess_thermal(self, frame):
        """Enhance thermal image for better detection"""
        # Convert to LAB color space
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge back
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return enhanced

    def run(self, state):
        cap = cv2.VideoCapture(state.video_path)
        state.start_session()

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Preprocess for thermal
            enhanced_frame = self.preprocess_thermal(frame)
            
            # Run detection on enhanced frame
            results = self.model(enhanced_frame, imgsz=640, conf=self.animal_confidence, verbose=False)
            
            human_detected = False
            animal_detected = False
            animal_count = 0
            detections = []  # Store all detections

            for r in results:
                for box in r.boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # For humans, use higher confidence threshold
                    if cls == HUMAN_CLASS and conf >= self.confidence:
                        human_detected = True
                        detections.append(('HUMAN', (x1, y1, x2, y2), conf))
                    
                    # For animals, use lower confidence (already filtered by model)
                    elif cls in ANIMAL_CLASSES:
                        animal_detected = True
                        animal_count += 1
                        label = self.get_animal_label(cls)
                        detections.append((label, (x1, y1, x2, y2), conf))

            # Draw detections on original frame (not enhanced)
            for label, (x1, y1, x2, y2), conf in detections:
                if label == 'HUMAN':
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                else:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # ALERT CONDITION: Only when BOTH human AND animal detected in same frame
            poaching_alert = human_detected and animal_detected

            state.update_frame(frame, human_detected, animal_count, poaching_alert)
            time.sleep(0.02)

        cap.release()
        state.end_session()

    def get_animal_label(self, cls):
        """Get readable label for animal class"""
        labels = {
            14: 'BIRD', 15: 'CAT', 16: 'DOG', 17: 'HORSE',
            18: 'SHEEP', 19: 'COW', 20: 'ELEPHANT', 21: 'BEAR',
            22: 'ZEBRA', 23: 'GIRAFFE'
        }
        return labels.get(cls, 'ANIMAL')