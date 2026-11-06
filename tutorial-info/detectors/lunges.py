import math

from core.base_exercise import BaseExercise


class LungesDetector(BaseExercise):
    DOWN_THRESHOLD = 100        # front knee angle at the bottom
    UP_THRESHOLD = 160          # front knee angle when standing
    BALANCE_TOLERANCE = 0.30    # sideways shoulder/hip shift as a fraction of torso length
    MIN_VISIBILITY = 0.7

    # side -> (shoulder, hip, knee, ankle) landmark indices
    SIDES = {
        "left": (11, 23, 25, 27),
        "right": (12, 24, 26, 28),
    }

    def process(self, landmarks):
        point = lambda idx: self.get_point(landmarks, idx)
        visible = lambda *idxs: all(landmarks[i].visibility >= self.MIN_VISIBILITY for i in idxs)

        knee_angles = {
            side: self.calculate_angle(point(hip), point(knee), point(ankle))
            for side, (_, hip, knee, ankle) in self.SIDES.items()
        }

       
        tracked = [
            side for side, (_, hip, knee, ankle) in self.SIDES.items()
            if visible(hip, knee, ankle)
        ]
        side = min(tracked or knee_angles, key=knee_angles.get)
        shoulder, hip, _, _ = self.SIDES[side]
        front_knee_angle = knee_angles[side]

        if tracked:
            if front_knee_angle <= self.DOWN_THRESHOLD:
                self.stage = "down"
            elif front_knee_angle >= self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1

        # Torso lean from vertical: 0 = upright
        hip_x, hip_y = point(hip)
        torso_angle = self.calculate_angle(point(shoulder), (hip_x, hip_y), (hip_x, hip_y - 1))

        return {
            "reps": self.reps,
            "front_knee_angle": round(front_knee_angle),
            "torso_angle": round(torso_angle),
            "balance_status": self._balance_status(landmarks),
        }

    def _balance_status(self, landmarks):
        shoulders_hips = [self.SIDES[s][i] for s in self.SIDES for i in (0, 1)]
        if any(landmarks[i].visibility < self.MIN_VISIBILITY for i in shoulders_hips):
            return "N/A"

        (ls, lh), (rs, rh) = (
            (landmarks[self.SIDES[s][0]], landmarks[self.SIDES[s][1]]) for s in ("left", "right")
        )
        shoulder_mid = ((ls.x + rs.x) / 2, (ls.y + rs.y) / 2)
        hip_mid = ((lh.x + rh.x) / 2, (lh.y + rh.y) / 2)

        torso_length = math.hypot(shoulder_mid[0] - hip_mid[0], shoulder_mid[1] - hip_mid[1]) or 1e-6
        sideways_shift = abs(shoulder_mid[0] - hip_mid[0]) / torso_length

        return "BALANCED" if sideways_shift <= self.BALANCE_TOLERANCE else "OFF BALANCE"
    

    