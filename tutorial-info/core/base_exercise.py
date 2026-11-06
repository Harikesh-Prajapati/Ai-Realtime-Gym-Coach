import math
from abc import ABC, abstractmethod


class BaseExercise(ABC):
    def __init__(self):
        self.reps = 0
        self.stage = None

    @staticmethod
    def calculate_angle(a, b, c):
        """Angle in degrees at point b, formed by points a-b-c."""
        ax, ay = a[0] - b[0], a[1] - b[1]
        cx, cy = c[0] - b[0], c[1] - b[1]

        magnitude = math.hypot(ax, ay) * math.hypot(cx, cy)
        if magnitude == 0:
            return 0.0

        cos_angle = (ax * cx + ay * cy) / magnitude
        return math.degrees(math.acos(max(-1.0, min(1.0, cos_angle))))

    @staticmethod
    def get_point(landmarks, idx):
        p = landmarks[idx]
        return p.x, p.y

    @abstractmethod
    def process(self, landmarks):
        """Analyse one frame of landmarks and update reps/stage/metrics."""

    def reset(self):
        """Reset counters. Subclasses can override and call super().reset()."""
        self.reps = 0
        self.stage = None
