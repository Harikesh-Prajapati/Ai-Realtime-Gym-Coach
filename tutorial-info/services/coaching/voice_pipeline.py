import time

import streamlit as st

MIN_GAP_S = 5                   
SQUAT_MAX_LEAN = 50                
MAJOR_EVENTS = {"workout_started", "set_completed", "workout_completed"}


ISSUE_RULES = {
    "Squats": [
        (lambda m: m.get("back_angle", 0) > SQUAT_MAX_LEAN,
         "The user is leaning too far forward during the squat."),
        (lambda m: m.get("depth_status") == "GO LOWER",
         "The user's squat is not deep enough - knees should bend more."),
    ],
    "Push-ups": [
        (lambda m: m.get("body_alignment") == "Poor Form",
         "The user's body is not straight during the push-up."),
        (lambda m: m.get("hip_status") == "SAGGING",
         "The user's hips are sagging down during the push-up."),
        (lambda m: m.get("hip_status") == "PIKED UP",
         "The user's hips are too high - lower them to form a straight line."),
    ],
    "Biceps Curls (Dumbbell)": [
        (lambda m: m.get("swing_status") == "SWINGING",
         "The user is swinging their torso during the curl - keep the body still."),
        (lambda m: m.get("shoulder_status") == "ELBOW DRIFTING",
         "The user's elbow is drifting away from their side during the curl."),
    ],
    "Shoulder Press": [
        (lambda m: m.get("back_arch_status") == "Excessive Arch",
         "The user is arching their lower back excessively during the press."),
        (lambda m: m.get("back_arch_status") == "Slight Arch",
         "Slight back arch detected - encourage the user to brace their core."),
    ],
    "Lunges": [
        (lambda m: m.get("balance_status") == "OFF BALANCE",
         "The user is losing balance during the lunge - keep the torso centered over the hips."),
    ],
}


class VoicePipeline:
    def __init__(self, llm, tts):
        self.llm = llm
        self.tts = tts
        self.last_spoken_at = 0

    @staticmethod
    def _find_form_issue(exercise, metrics):
        if "issue" in metrics:
            return metrics["issue"]

        for is_problem, message in ISSUE_RULES.get(exercise, []):
            if is_problem(metrics):
                return message
        return None

    def process_event(self, event, exercise, metrics):
        """Return (audio_bytes, text) for the cue, or None if there is nothing to say."""
        issue = None

        if event not in MAJOR_EVENTS:
            
            issue = self._find_form_issue(exercise, metrics)
            if not issue or time.time() - self.last_spoken_at < MIN_GAP_S:
                return None

        text = self.llm.give_feedback(event, issue)
        if not text:
            return None

        self.last_spoken_at = time.time()
        return self.tts.speak(text), text


def autoplay_audio(audio_bytes):
    if not audio_bytes:
        return

    
    st.markdown("<style>[data-testid='stAudio'] {display: none;}</style>", unsafe_allow_html=True)
    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
