from core.base_exercise import BaseExercise


class BicepsCurlDetector(BaseExercise):
    UP_THRESHOLD = 50           # elbow angle at the top of the curl
    DOWN_THRESHOLD = 160        # elbow angle with the arm hanging
    ELBOW_DRIFT_TOLERANCE = 20  # degrees the upper arm may move away from vertical
    SWING_THRESHOLD = 15        # degrees the torso may lean from vertical
    MIN_VISIBILITY = 0.7

    # side -> (shoulder, elbow, wrist, hip) landmark indices
    SIDES = {
        "left": (11, 13, 15, 23),
        "right": (12, 14, 16, 24),
    }

    def process(self, landmarks):
        # Track the arm the camera sees best
        left_elbow, right_elbow = self.SIDES["left"][1], self.SIDES["right"][1]
        side = "left" if landmarks[left_elbow].visibility >= landmarks[right_elbow].visibility else "right"
        shoulder, elbow, wrist, _ = self.SIDES[side]

        point = lambda idx: self.get_point(landmarks, idx)

        elbow_angle = self.calculate_angle(point(shoulder), point(elbow), point(wrist))

        shoulder_status = "N/A"
        if self._visible(landmarks, shoulder, elbow, wrist):
            if elbow_angle <= self.UP_THRESHOLD:
                self.stage = "up"
            elif elbow_angle >= self.DOWN_THRESHOLD and self.stage == "up":
                self.stage = "down"
                self.reps += 1

            # Upper arm angle from vertical: 0 = hanging straight down
            sx, sy = point(shoulder)
            upper_arm_angle = self.calculate_angle(point(elbow), (sx, sy), (sx, sy + 1))
            shoulder_status = (
                "STABLE" if upper_arm_angle <= self.ELBOW_DRIFT_TOLERANCE else "ELBOW DRIFTING"
            )

        return {
            "reps": self.reps,
            "elbow_angle": round(elbow_angle),
            "shoulder_status": shoulder_status,
            "swing_status": self._swing_status(landmarks),
        }

    def _visible(self, landmarks, *idxs):
        return all(landmarks[i].visibility >= self.MIN_VISIBILITY for i in idxs)

    def _swing_status(self, landmarks):
        shoulders = [self.SIDES[s][0] for s in self.SIDES]
        hips = [self.SIDES[s][3] for s in self.SIDES]

        
        if not self._visible(landmarks, *shoulders, *hips):
            return "N/A"

        def mid(idxs):
            return (
                sum(landmarks[i].x for i in idxs) / len(idxs),
                sum(landmarks[i].y for i in idxs) / len(idxs),
            )

        shoulder_mid, hip_mid = mid(shoulders), mid(hips)

        
        lean = self.calculate_angle(shoulder_mid, hip_mid, (hip_mid[0], hip_mid[1] - 1))

        return "NO SWING" if lean <= self.SWING_THRESHOLD else "SWINGING"
    
