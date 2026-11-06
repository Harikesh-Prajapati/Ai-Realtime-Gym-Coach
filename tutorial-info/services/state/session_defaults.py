import streamlit as st

from services.config.workout_config import METRICS_FIELDS


METRIC_DEFAULTS = {
    key: default
    for fields in METRICS_FIELDS.values()
    for key, default in fields.items()
}


def initial_session_defaults():
    """Create any missing session keys without overwriting existing values."""
    defaults = {
       
        "plan_exercise": "Squats",
        "plan_sets": 3,
        "plan_reps": 10,

        # Running workout
        "workout_started": False,
        "exercise_type": None,
        "target_sets": 0,
        "reps_per_set": 0,
        "reps": 0,
        "current_set_reps": 0,
        "sets_completed": 0,
        "workout_completed": False,
        "set_cycle_started_at": 0.0,
        "last_saved_sets_completed": 0,
        "last_notified_workout_complete": False,

        
        "audio_to_play": None,
        "coach_feedback": None,

        **METRIC_DEFAULTS,
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)