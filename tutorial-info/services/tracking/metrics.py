import time

import streamlit as st

from services.config.workout_config import METRICS_FIELDS
from services.persistence.exercise_repository import add_exercise


FORM_CHECK_INTERVAL_S = 8
NO_POSE_METRICS = {"issue": "No pose detected! Please step into the camera frame."}


def _speak(event, exercise, metrics):
    """Ask the voice coach for a cue and store the audio/text for the page."""
    pipeline = st.session_state.get("voice_pipeline")
    if not pipeline:
        return

    try:
        result = pipeline.process_event(event=event, exercise=exercise, metrics=metrics)
    except Exception as e:
        st.session_state.voice_error = str(e)
        return

    if result:
        st.session_state.audio_to_play, st.session_state.coach_feedback = result


def _save_sets(exercise, new_sets, reps_per_set):
    ss = st.session_state
    now = time.time()
    seconds = round(now - ss.get("set_cycle_started_at", now))

    
    user_id = ss.get("user_id")
    if isinstance(user_id, int) and user_id > 0:
        add_exercise(user_id, exercise, new_sets * reps_per_set, new_sets, seconds)

    ss.set_cycle_started_at = now


def _idle_event(pose_detected):
    """Pick a periodic cue, at most once per FORM_CHECK_INTERVAL_S."""
    ss = st.session_state
    now = time.time()
   
    last = max(ss.get("last_form_check_at", 0), ss.get("set_cycle_started_at", 0))

    if now - last < FORM_CHECK_INTERVAL_S:
        return None

    ss.last_form_check_at = now
    return "ongoing_form_check" if pose_detected else "no_pose_detected"


def sync_metrics_update(context):
    """Copy live metrics into session state, save finished sets and trigger coach cues."""
    if not context or not context.state.playing:
        return

    processor = getattr(context, "video_processor", None)
    exercise = st.session_state.get("exercise_type")
    if not processor or not exercise:
        return

    processor.set_exercise(exercise)
    latest = processor.get_latest_metrics()
    fields = METRICS_FIELDS.get(exercise)
    if not latest or not fields:
        return

    ss = st.session_state

    reps = latest.get("reps") or 0
    ss.reps = reps
    for key, default in fields.items():
        ss[key] = latest.get(key, default)

    # Progress
    reps_per_set = ss.get("reps_per_set", 0)
    target_sets = ss.get("target_sets", 0)
    valid_plan = reps_per_set > 0 and target_sets > 0

    sets_completed = min(reps // reps_per_set, target_sets) if valid_plan else 0
    workout_completed = valid_plan and sets_completed >= target_sets

    ss.sets_completed = sets_completed
    ss.current_set_reps = reps % reps_per_set if valid_plan else 0
    ss.workout_completed = workout_completed

    
    event = None

    last_saved = ss.get("last_saved_sets_completed", 0)
    if sets_completed > last_saved:
        _save_sets(exercise, sets_completed - last_saved, reps_per_set)
        ss.last_saved_sets_completed = sets_completed
        event = "set_completed"

    if workout_completed and not ss.get("last_notified_workout_complete", False):
        ss.last_notified_workout_complete = True
        event = "workout_completed"
    elif event is None and not workout_completed:
        event = _idle_event(latest.get("pose_detected", True))

    if event:
        _speak(event, exercise, NO_POSE_METRICS if event == "no_pose_detected" else latest)
