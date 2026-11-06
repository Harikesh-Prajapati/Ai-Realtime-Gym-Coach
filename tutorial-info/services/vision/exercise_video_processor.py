import threading
import time
from pathlib import Path

import av
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from streamlit_webrtc import VideoProcessorBase

from detectors.squat import SquatDetector
from detectors.pushup import PushUpDetector
from detectors.biceps_curl import BicepsCurlDetector
from detectors.shoulder_press import ShoulderPressDetector
from detectors.lunges import LungesDetector
from services.config.workout_config import POSE_CONNECTIONS


MODEL_PATH = Path(__file__).resolve().parents[2] / "ml_models" / "pose_landmarker_full.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_full/float16/latest/pose_landmarker_full.task"
)

MIN_VISIBILITY = 0.7
GREEN = (0, 255, 0)  # BGR
BLUE = (255, 0, 0)   # BGR
FONT = cv2.FONT_HERSHEY_SIMPLEX

# exercise -> lines of feedback text drawn on the video
OVERLAY_LINES = {
    "Squats": lambda m: [f"DEPTH: {m['depth_status']}"],
    "Push-ups": lambda m: [f"BODY: {m['body_alignment']}", f"HIP: {m['hip_status']}"],
    "Biceps Curls (Dumbbell)": lambda m: [f"SWING: {m['swing_status']}"],
    "Shoulder Press": lambda m: [f"EXT: {m['extension_status']}", f"BACK: {m['back_arch_status']}"],
    "Lunges": lambda m: [f"BALANCE: {m['balance_status']}"],
}


class VideoProcessorClass(VideoProcessorBase):
    def __init__(self):
        self._lock = threading.Lock()
        self._latest_metrics = None
        self._exercise_type = "Squats"
        self._reset_pending = False
        self._last_timestamp_ms = 0

        if not MODEL_PATH.is_file():
            raise FileNotFoundError(
                f"Pose model not found at {MODEL_PATH}. Download it from {MODEL_URL} "
                "and save it in the ml_models folder."
            )

        options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(MODEL_PATH)),
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=0.7,
            min_pose_presence_confidence=0.7,
            min_tracking_confidence=0.7,
            output_segmentation_masks=False,
        )
        self._landmarker = vision.PoseLandmarker.create_from_options(options)

        self._detectors = {
            "Squats": SquatDetector(),
            "Push-ups": PushUpDetector(),
            "Biceps Curls (Dumbbell)": BicepsCurlDetector(),
            "Shoulder Press": ShoulderPressDetector(),
            "Lunges": LungesDetector(),
        }

    

    def set_latest_metrics(self, metrics):
        with self._lock:
            self._latest_metrics = metrics.copy()

    def get_latest_metrics(self):
        with self._lock:
            return None if self._latest_metrics is None else self._latest_metrics.copy()

    def set_exercise(self, exercise_type):
        with self._lock:
            if exercise_type != self._exercise_type:
                self._exercise_type = exercise_type
                self._reset_pending = True  

    def get_exercise(self):
        with self._lock:
            return self._exercise_type

    def _take_exercise(self):
        """Return (exercise, needs_reset) and clear the reset flag."""
        with self._lock:
            exercise, reset = self._exercise_type, self._reset_pending
            self._reset_pending = False
        return exercise, reset

   

    @staticmethod
    def _draw_skeleton(img, landmarks):
        h, w = img.shape[:2]

        for start_idx, end_idx in POSE_CONNECTIONS:
            p1, p2 = landmarks[start_idx], landmarks[end_idx]
            if p1.visibility > MIN_VISIBILITY and p2.visibility > MIN_VISIBILITY:
                cv2.line(img, (int(p1.x * w), int(p1.y * h)), (int(p2.x * w), int(p2.y * h)), GREEN, 8)

        for lm in landmarks:
            if lm.visibility > MIN_VISIBILITY:
                cv2.circle(img, (int(lm.x * w), int(lm.y * h)), 8, BLUE, -1)

    @staticmethod
    def _draw_text(img, text, x, y, scale=0.9):
        cv2.putText(img, text, (x, y), FONT, scale, GREEN, 2, cv2.LINE_AA)

    def _draw_no_pose_warning(self, img):
        self._draw_text(img, "NO POSE DETECTED", 30, 50, scale=1)
        self._draw_text(img, "KEEP YOUR FULL BODY IN VIEW", 30, 100, scale=1)

    def _draw_overlays(self, img, metrics, exercise):
        make_lines = OVERLAY_LINES.get(exercise)
        if not make_lines:
            return

        h = img.shape[0]
        
        for i, line in enumerate(reversed(make_lines(metrics))):
            self._draw_text(img, line, 20, h - 20 - i * 35)

  

    def _next_timestamp_ms(self):
        """MediaPipe needs strictly increasing timestamps in VIDEO mode."""
        self._last_timestamp_ms = max(int(time.monotonic() * 1000), self._last_timestamp_ms + 1)
        return self._last_timestamp_ms

    def recv(self, frame):
        image = cv2.flip(frame.to_ndarray(format="bgr24"), 1)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=cv2.cvtColor(image, cv2.COLOR_BGR2RGB),
        )
        result = self._landmarker.detect_for_video(mp_image, self._next_timestamp_ms())

        exercise, reset = self._take_exercise()
        detector = self._detectors.get(exercise)

        if detector and reset:
            detector.reset()

        if result.pose_landmarks and detector:
            landmarks = result.pose_landmarks[0]
            self._draw_skeleton(image, landmarks)

            metrics = detector.process(landmarks)
            metrics["pose_detected"] = True

            self._draw_overlays(image, metrics, exercise)
            self.set_latest_metrics(metrics)
        else:
            self._draw_no_pose_warning(image)

            
            with self._lock:
                self._latest_metrics = {**(self._latest_metrics or {}), "pose_detected": False}

        return av.VideoFrame.from_ndarray(image, format="bgr24")