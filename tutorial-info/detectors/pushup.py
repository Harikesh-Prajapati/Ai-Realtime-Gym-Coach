import math

from core.base_exercise import BaseExercise


class PushUpDetector(BaseExercise):
    DOWN_THRESHOLD = 90         # elbow angle at the bottom
    UP_THRESHOLD = 160          # elbow angle at the top
    BODY_STRAIGHT = 160         # shoulder-hip-ankle angle
    BODY_SLIGHT_BEND = 140
    HIP_SAG_TOLERANCE = 0.08    # hip offset as a fraction of shoulder-to-ankle length
    MIN_VISIBILITY = 0.7

    # side -> (shoulder, elbow, wrist, hip, ankle) landmark indices
    SIDES = {
        "left": (11, 13, 15, 23, 27),
        "right": (12, 14, 16, 24, 28),
    }

    def process(self, landmarks):
        # Track the side the camera sees best
        left_elbow, right_elbow = self.SIDES["left"][1], self.SIDES["right"][1]
        side = "left" if landmarks[left_elbow].visibility >= landmarks[right_elbow].visibility else "right"
        shoulder, elbow, wrist, hip, ankle = self.SIDES[side]

        point = lambda idx: self.get_point(landmarks, idx)
        visible = lambda *idxs: all(landmarks[i].visibility >= self.MIN_VISIBILITY for i in idxs)

        elbow_angle = self.calculate_angle(point(shoulder), point(elbow), point(wrist))

        # Rep counting only needs the arm
        if visible(shoulder, elbow, wrist):
            if elbow_angle <= self.DOWN_THRESHOLD:
                self.stage = "down"
            elif elbow_angle >= self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1

        # Form feedback needs the whole body line
        body_alignment, hip_status = "N/A", "N/A"
        if visible(shoulder, hip, ankle):
            body_alignment = self._body_alignment(
                self.calculate_angle(point(shoulder), point(hip), point(ankle))
            )
            hip_status = self._hip_status(landmarks[shoulder], landmarks[hip], landmarks[ankle])

        return {
            "reps": self.reps,
            "elbow_angle": round(elbow_angle),
            "body_alignment": body_alignment,
            "hip_status": hip_status,
        }

    def _body_alignment(self, body_angle):
        if body_angle >= self.BODY_STRAIGHT:
            return "Straight"
        if body_angle >= self.BODY_SLIGHT_BEND:
            return "Slight Bend"
        return "Poor Form"

    def _hip_status(self, shoulder, hip, ankle):
        
        body_length = math.hypot(ankle.x - shoulder.x, ankle.y - shoulder.y) or 1e-6
        deviation = (hip.y - (shoulder.y + ankle.y) / 2) / body_length

        if deviation > self.HIP_SAG_TOLERANCE:
            return "SAGGING"
        if deviation < -self.HIP_SAG_TOLERANCE:
            return "PIKED UP"
        return "LEVEL"
    
