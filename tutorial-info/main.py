import streamlit as st
import os
import time
from pathlib import Path
import pandas as pd
from services.auth.login_wall import render_login_wall
from services.state.session_defaults import initial_session_defaults
from services.config.workout_config import EXERCISE_OPTIONS
from services.ui.exercise_guide import render_exercise_guide
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles
from services.persistence.exercise_repository import init_db, get_users_exercises
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from services.vision.exercise_video_processor import VideoProcessorClass
from services.tracking.metrics import sync_metrics_update
from openai import OpenAI
from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech
from services.coaching.voice_pipeline import VoicePipeline, autoplay_audio


BASE_DIR = Path(__file__).resolve().parent  

ENV_FILE = BASE_DIR / ".env"


def load_env_file(path: Path) -> None:
    """Read KEY=value lines from a .env file into the environment (no extra package needed)."""
    try:
       
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeDecodeError):
        return 

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip().removeprefix("export ").strip()
        if key:
            os.environ[key] = value.strip().strip('"').strip("'")


load_env_file(ENV_FILE)


def missing_key_message() -> str:
    """Explain exactly why OPENAI_API_KEY was not found."""
    if not ENV_FILE.is_file():
        if (BASE_DIR / ".env.txt").is_file():
            return "Your file is named `.env.txt`. Rename it to exactly `.env`."
        return f"No .env file found. Create `{ENV_FILE}` containing `OPENAI_API_KEY=your-key`."
    if ENV_FILE.read_bytes()[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return "The .env file is saved as UTF-16. Re-save it as UTF-8 (Notepad: Save As, Encoding: UTF-8)."
    return "The .env file has no `OPENAI_API_KEY` line. Check the name is spelled exactly like that."


def get_openai_api_key() -> str:
    """Read the key from the environment/.env first, then from Streamlit secrets."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip().strip('"')
    if api_key:
        return api_key
    try:
        
        return st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        return ""


def init_voice_pipeline():
    """Create the voice pipeline once per session and remember why it failed."""
   
    if st.session_state.get("voice_pipeline") is not None:
        return

    st.session_state.voice_error = None
    try:
        api_key = get_openai_api_key()
        if not api_key:
            raise ValueError(missing_key_message())

        openai_client = OpenAI(api_key=api_key)
        llm_coach = LLMCoach(openai_client)
        tts = TextToSpeech()
        st.session_state.voice_pipeline = VoicePipeline(llm_coach, tts)
    except Exception as e:
        st.session_state.voice_pipeline = None
        st.session_state.voice_error = str(e)


def fire_event(event: str, exercise, metrics=None):
    """Send an event to the voice coach and store audio/text if returned."""
    pipeline = st.session_state.get("voice_pipeline")
    if not pipeline:
        return
    try:
        result = pipeline.process_event(
            event=event,
            exercise=exercise,
            metrics=metrics or {}
        )
    except Exception as e:
        st.session_state.voice_error = str(e)
        return

    if result:
        st.session_state.audio_to_play, st.session_state.coach_feedback = result


def end_workout():
    st.session_state.workout_started = False
    st.session_state.camera_seen_playing = False


def render_sidebar(workout_started: bool):
    with st.sidebar:
        st.title("🏋️‍♂️ Apna AI Coach")

        username = st.session_state.get("username")
        if username:
            st.caption(f"👤 Login as {username}")

        if st.button("Log out", key="logout_button", width="stretch"):
            st.session_state.clear()  
            st.rerun()

        if st.session_state.get("voice_pipeline") is None:
            err = st.session_state.get("voice_error")
            st.warning(f"Voice coach disabled: {err}" if err else "Voice coach disabled")

        st.divider()
        st.subheader("Workout Plan")

        if not workout_started:
            plan_exercise = st.selectbox("Exercise", options=EXERCISE_OPTIONS, key="plan_exercise")
            plan_sets = st.number_input("Sets", min_value=1, max_value=50, key="plan_sets", step=1)
            plan_reps = st.number_input("Reps per Set", min_value=1, max_value=50, key="plan_reps", step=1)

            st.markdown("")

            if st.button("Start Workout", width="stretch", key="start_session_button"):
                st.session_state.exercise_type = plan_exercise
                st.session_state.target_sets = int(plan_sets)
                st.session_state.reps_per_set = int(plan_reps)
                st.session_state.reps = 0
                st.session_state.workout_started = True
                st.session_state.camera_seen_playing = False
                st.session_state.set_cycle_started_at = time.time()
                st.session_state.last_saved_sets_completed = 0
                st.session_state.last_notified_workout_complete = False

                
                st.session_state.audio_to_play = None
                st.session_state.coach_feedback = None

                fire_event("workout_started", plan_exercise)
                st.rerun()
        else:
            exercise = st.session_state.get("exercise_type")
            sets = st.session_state.get("target_sets")
            reps = st.session_state.get("reps_per_set")

            st.info(f"**{exercise}** -- {sets} Sets / {reps} Reps")

            if st.button("End Workout", key="end_session_button", width="stretch"):
                finished_all = (
                    st.session_state.get("sets_completed", 0)
                    >= st.session_state.get("target_sets", 1)
                )
                end_workout()
                st.session_state.audio_to_play = None
                st.session_state.coach_feedback = None

                
                if finished_all:
                    fire_event("workout_completed", exercise)

                st.rerun()

        if workout_started:
            render_progress(st.session_state.get("exercise_type"))


def render_progress(exercise):
    ss = st.session_state
    st.divider()
    st.subheader("Progress")

    st.metric("Total Reps", f"{ss.get('reps', 0)}")
    st.metric("Current Set Reps", f"{ss.get('current_set_reps', 0)} / {ss.get('reps_per_set', 0)}")
    st.metric("Sets Completed", f"{ss.get('sets_completed', 0)} / {ss.get('target_sets', 0)}")

    st.divider()

    if exercise == "Squats":
        st.subheader("Squat Metrics")
        st.metric("Knee Angle", f"{ss.get('knee_angle', 0)}°")
        st.metric("Back Angle", f"{ss.get('back_angle', 0)}°")
        st.metric("Depth Status", ss.get("depth_status", "-"))

    elif exercise == "Push-ups":
        st.subheader("Push-up Metrics")
        st.metric("Elbow Angle", f"{ss.get('elbow_angle', 0)}°")
        st.metric("Body Alignment", ss.get("body_alignment", "-"))
        st.metric("Hip Position", ss.get("hip_status", "-"))

    elif exercise == "Biceps Curls (Dumbbell)":
        st.subheader("Curl Metrics")
        st.metric("Elbow Angle", f"{ss.get('elbow_angle', 0)}°")
        st.metric("Shoulder Stability", ss.get("shoulder_status", "-"))
        st.metric("Swing Detection", ss.get("swing_status", "-"))

    elif exercise == "Shoulder Press":
        st.subheader("Shoulder Press Metrics")
        st.metric("Elbow Angle", f"{ss.get('elbow_angle', 0)}°")
        st.metric("Arm Extension", ss.get("extension_status", "-"))
        st.metric("Back Arch", ss.get("back_arch_status", "-"))

    elif exercise == "Lunges":
        st.subheader("Lunge Metrics")
        st.metric("Front Knee Angle", f"{ss.get('front_knee_angle', 0)}°")
        st.metric("Torso Angle", f"{ss.get('torso_angle', 0)}°")
        st.metric("Balance Status", ss.get("balance_status", "-"))


def render_history():
    st.divider()
    st.markdown("#### Workout History")

    user_id = st.session_state.get("user_id", 0)

    if not isinstance(user_id, int):
        st.info("Workout history is available for registered users only.")
        return

    history_rows = get_users_exercises(user_id)

    arr = [
        {
            "Exercise": row["exercise_name"],
            "Reps": row["reps"],
            "Sets": row["sets"],
            "Time (sec)": row["time"],
            "Date": row["created_at"],
        }
        for row in history_rows
    ]

    df = pd.DataFrame(arr)

    if df.empty:
        st.info("No workout history found.")
        return

   
    df["Date"] = (
        pd.to_datetime(df["Date"], utc=True)
        .dt.tz_convert("Asia/Kolkata")
        .dt.date
    )

    agg_df = (
        df.groupby(["Exercise", "Date"])
        .agg({"Reps": "sum", "Sets": "sum", "Time (sec)": "sum"})
        .reset_index()
    )
    agg_df.index += 1
    st.table(agg_df, border="horizontal")


def main():
    st.set_page_config(
        page_icon="🏋️‍♀️",
        page_title="AI Real-time GYM Coach",
        initial_sidebar_state="expanded",
        layout="wide",
    )

    load_css(BASE_DIR / "static" / "style.css")
    inject_local_font(BASE_DIR / "static" / "AdobeClean.otf", "AdobeClean")

    init_db()

    if not render_login_wall():
        return

    initial_session_defaults()
    init_voice_pipeline()

    workout_started = st.session_state.get("workout_started", False)

    render_sidebar(workout_started)

    st.title("AI Real-time GYM Coach")
    st.markdown("#### Real-time pose detection with proactive AI voice coaching")

    if st.session_state.get("audio_to_play"):
        autoplay_audio(st.session_state.audio_to_play)

    if st.session_state.get("coach_feedback"):
        st.markdown("")
        st.success(f"🤖 **Coach:** {st.session_state.coach_feedback}")

    video_col, guide_col = st.columns([5, 3], gap="medium")


    with guide_col:
        render_exercise_guide(
            st.session_state.get("exercise_type") if workout_started
            else st.session_state.get("plan_exercise")
        )

    with video_col:
        render_video_panel(workout_started)

    render_history()


def render_video_panel(workout_started: bool):
    """The start prompt before a workout, the live camera during one."""
    if not workout_started:
        st.markdown(
            """
            <div style="
                border: 10px dashed #444;
                border-radius: 0px;
                padding: 48px 32px;
                text-align: center;
                color: #888;
                margin-top: 32px;
                margin-bottom: 32px;
            ">
                <h2 style="color:#ccc; margin-bottom:8px;">👈 Set your workout plan</h2>
                <p style="font-size:1.05rem;">
                    Choose your exercise, sets and reps in the sidebar,<br>
                    then click <strong>Start Workout</strong> to activate the camera and AI coach.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        context = webrtc_streamer(
            key="exercise-analysis",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=VideoProcessorClass,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            media_stream_constraints={
                "video": {
                    "width": {"ideal": 1280},
                    "height": {"ideal": 720},
                    "frameRate": {"ideal": 30},
                },
                "audio": False,
            },
           
            desired_playing_state=None if st.session_state.get("camera_seen_playing") else True,
          
            video_html_attrs={
                "autoPlay": True,
                "controls": False,
                "muted": True,
                "style": {"width": "100%"},
            },
            async_processing=True,
        )

       
        inject_webrtc_styles()

        if context.state.playing:
            st.session_state.camera_seen_playing = True
        elif st.session_state.get("camera_seen_playing"):
            
            end_workout()
            st.rerun()

        sync_metrics_update(context)

        if context.state.playing:
            time.sleep(0.25)
            st.rerun()


if __name__ == "__main__":
    main()