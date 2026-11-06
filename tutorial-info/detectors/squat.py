from core.base_exercise import BaseExercise


class SquatDetector(BaseExercise):
    DOWN_THRESHOLD = 100   # knee angle at or below this = good depth
    UP_THRESHOLD = 160     # knee angle at or above this = standing
    MIN_VISIBILITY = 0.7

    # side -> (shoulder, hip, knee, ankle) landmark indices
    SIDES = {
        "left": (11, 23, 25, 27),
        "right": (12, 24, 26, 28),
    }

    def process(self, landmarks):
        # Track the side the camera sees best
        left_knee, right_knee = self.SIDES["left"][2], self.SIDES["right"][2]
        side = "left" if landmarks[left_knee].visibility >= landmarks[right_knee].visibility else "right"
        shoulder, hip, knee, ankle = self.SIDES[side]

        point = lambda idx: self.get_point(landmarks, idx)

        knee_angle = self.calculate_angle(point(hip), point(knee), point(ankle))
        back_angle = self.calculate_angle(point(shoulder), point(hip), point(knee))

        visible = all(
            landmarks[idx].visibility >= self.MIN_VISIBILITY for idx in (hip, knee, ankle)
        )

        if visible:
            if knee_angle <= self.DOWN_THRESHOLD:
                self.stage = "down"
            elif knee_angle >= self.UP_THRESHOLD:
                if self.stage == "down":
                    self.reps += 1
                self.stage = "up"

        return {
            "reps": self.reps,
            "knee_angle": round(knee_angle),
            "back_angle": round(back_angle),
            "depth_status": self._depth_status(knee_angle, visible),
        }

    def _depth_status(self, knee_angle, visible):
        if not visible:
            return "N/A"
        if knee_angle >= self.UP_THRESHOLD:
            return "STANDING"
        if knee_angle <= self.DOWN_THRESHOLD:
            return "GOOD DEPTH"
        
        return "STAND UP" if self.stage == "down" else "GO LOWER"
    