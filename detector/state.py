import cv2
import threading
import base64
import time

class AppState:
    def __init__(self):
        self.lock = threading.Lock()
        self.running = False
        self.completed = False
        self.video_path = None
        self.latest_frame = None
        self.human_frames = []  # Frames with BOTH human+animal (alerts)
        self.human_count = 0
        self.animal_count = 0
        self.alert_count = 0  # Count of poaching alerts (human+animal)
        self.alert_pending = False  # Flag for frontend to trigger sound
        self.start_time = None
        self.end_time = None
        self.filename = None

    def set_video(self, path, filename=None):
        with self.lock:
            self.video_path = path
            self.filename = filename or "video"
            self.human_frames.clear()
            self.latest_frame = None
            self.human_count = 0
            self.animal_count = 0
            self.alert_count = 0
            self.alert_pending = False
            self.completed = False
            self.start_time = None
            self.end_time = None

    def start_session(self):
        with self.lock:
            self.start_time = time.time()
            self.running = True
            self.completed = False

    def end_session(self):
        with self.lock:
            self.end_time = time.time()
            self.running = False
            self.completed = True

    def update_frame(self, frame, human=False, animal_count=0, alert=False):
        with self.lock:
            self.latest_frame = frame.copy()
            if animal_count > 0:
                self.animal_count += animal_count
            if human:
                self.human_count += 1
            # Only save frame and trigger alert when BOTH human AND animal detected
            if alert:
                self.alert_count += 1
                self.alert_pending = True  # Signal frontend to play sound
                _, buf = cv2.imencode(".jpg", frame)
                self.human_frames.append(
                    base64.b64encode(buf).decode()
                )

    def stream(self):
        while True:
            with self.lock:
                if self.latest_frame is None:
                    # Return a placeholder black frame
                    placeholder = cv2.imencode(".jpg", 
                        __import__('numpy').zeros((480, 640, 3), dtype='uint8'))[1]
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" +
                        placeholder.tobytes() + b"\r\n"
                    )
                else:
                    _, buf = cv2.imencode(".jpg", self.latest_frame)
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" +
                        buf.tobytes() + b"\r\n"
                    )
            time.sleep(0.03)  # ~30fps, prevent CPU overload

    def get_human_frames(self):
        with self.lock:
            return self.human_frames
    
    def get_stats(self):
        with self.lock:
            duration = ""
            if self.start_time:
                elapsed = (self.end_time or time.time()) - self.start_time
                mins = int(elapsed // 60)
                secs = int(elapsed % 60)
                duration = f"{mins:02d}:{secs:02d}"
            
            # Check and clear alert_pending (frontend will play sound)
            should_alert = self.alert_pending
            self.alert_pending = False  # Clear after reading
            
            return {
                "humans": self.human_count,
                "animals": self.animal_count,
                "alerts": self.alert_count,
                "frames": self.human_frames,
                "running": self.running,
                "completed": self.completed,
                "duration": duration,
                "filename": self.filename,
                "thumbnail": self.human_frames[0] if self.human_frames else None,
                "alert_pending": should_alert  # Frontend uses this to sync sound
            }