METRICS_FIELDS = {
    "Squats": {
        "knee_angle": 0,
        "back_angle": 0,
        "depth_status": "N/A",
    },
    "Push-ups": {
        "elbow_angle": 0,
        "body_alignment": "N/A",
        "hip_status": "N/A",
    },
    "Biceps Curls (Dumbbell)": {
        "elbow_angle": 0,
        "shoulder_status": "N/A",
        "swing_status": "N/A",
    },
    "Shoulder Press": {
        "elbow_angle": 0,
        "extension_status": "N/A",
        "back_arch_status": "N/A",
    },
    "Lunges": {
        "front_knee_angle": 0,
        "torso_angle": 0,
        "balance_status": "N/A",
    },
}


EXERCISE_OPTIONS = list(METRICS_FIELDS)


POSE_CONNECTIONS = [
    # Shoulders and arms
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    # Torso and hips
    (11, 23), (12, 24), (23, 24),
    # Legs and feet
    (23, 25), (25, 27), (27, 29), (29, 31), (27, 31),
    (24, 26), (26, 28), (28, 30), (30, 32), (28, 32),
]

PROMPT = """You are Apna AI Coach, an AI gym trainer watching a user's workout through a live camera.
Your replies are spoken aloud, so write 10-15 words of natural, energetic speech. Plain text only: no emojis, markdown or lists.

You receive messages like: "Event: <event> Form Issue: <description>"
Events: workout_started, set_completed, workout_completed, no_pose_detected, ongoing_form_check.
The form issue is a technical description of a pose error, if there is one.

Rules:
- Speak directly to the user ("Straighten your back"), never about them in the third person.
- No greetings and no questions. Stay focused on the workout.
- Keep a professional, encouraging tone and put safety first.
- Never mention "N/A" or missing data.

Respond by event:
- workout_started: a sharp, motivating command to begin.
- set_completed: direct praise for finishing the set.
- workout_completed: a warm, encouraging close to the session.
- no_pose_detected: a clear instruction to move so the whole body is in the camera frame.
- ongoing_form_check with a form issue: a precise, supportive correction for that error.
- ongoing_form_check with no issue: a few energetic words of encouragement.
"""