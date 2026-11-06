from core.base_exercise import BaseExercise


class ShoulderPressDetector(BaseExercise):
    UP_THRESHOLD = 160          
    NEAR_UP_THRESHOLD = 130     
    DOWN_THRESHOLD = 90         
    BACK_NEUTRAL = 160          
    BACK_SLIGHT_ARCH = 140
    MIN_VISIBILITY = 0.7

    # side -> (shoulder, elbow, wrist, hip, knee) landmark indices
    SIDES = {
        "left": (11, 13, 15, 23, 25),
        "right": (12, 14, 16, 24, 26),
    }

    def process(self, landmarks):
        # Track the side the camera sees best
        left_elbow, right_elbow = self.SIDES["left"][1], self.SIDES["right"][1]
        side = "left" if landmarks[left_elbow].visibility >= landmarks[right_elbow].visibility else "right"
        shoulder, elbow, wrist, hip, knee = self.SIDES[side]

        point = lambda idx: self.get_point(landmarks, idx)
        visible = lambda *idxs: all(landmarks[i].visibility >= self.MIN_VISIBILITY for i in idxs)

        elbow_angle = self.calculate_angle(point(shoulder), point(elbow), point(wrist))
        arm_visible = visible(shoulder, elbow, wrist)

        if arm_visible:
            if elbow_angle >= self.UP_THRESHOLD:
                self.stage = "up"
            elif elbow_angle <= self.DOWN_THRESHOLD and self.stage == "up":
                self.stage = "down"
                self.reps += 1

        # The back angle needs hip and knee, which are often out of frame
        back_arch_status = "N/A"
        if visible(shoulder, hip, knee):
            back_angle = self.calculate_angle(point(shoulder), point(hip), point(knee))
            if back_angle >= self.BACK_NEUTRAL:
                back_arch_status = "Neutral"
            elif back_angle >= self.BACK_SLIGHT_ARCH:
                back_arch_status = "Slight Arch"
            else:
                back_arch_status = "Excessive Arch"

        return {
            "reps": self.reps,
            "elbow_angle": round(elbow_angle),
            "extension_status": self._extension_status(elbow_angle, arm_visible),
            "back_arch_status": back_arch_status,
        }

    def _extension_status(self, elbow_angle, arm_visible):
        if not arm_visible:
            return "N/A"
        if elbow_angle >= self.UP_THRESHOLD:
            return "FULL EXTENSION"
        if elbow_angle >= self.NEAR_UP_THRESHOLD:
            return "NEARLY EXTENDED"
        if elbow_angle > self.DOWN_THRESHOLD:
            return "PRESSING"
        return "START POSITION"
    
