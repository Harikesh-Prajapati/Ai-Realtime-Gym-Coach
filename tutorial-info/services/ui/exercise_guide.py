import re
from functools import lru_cache
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


CUSTOM_IMAGE_DIR = Path(__file__).resolve().parents[2] / "static" / "exercises"
IMAGE_EXTENSIONS = ("gif", "png", "jpg", "jpeg", "webp")

DEMO_HEIGHT = 340
LOOP_SECONDS = 3.6

KEY_TIMES = "0;0.15;0.5;0.65;1"
KEY_SPLINES = "0 0 1 1;0.45 0 0.2 1;0 0 1 1;0.45 0 0.2 1"

GUIDES = {
    "Squats": {
        "steps": [
            "Stand with your feet shoulder-width apart.",
            "Push your hips back and bend your knees, keeping your chest up.",
            "Lower until your thighs are about parallel to the floor.",
            "Press through your heels to stand back up.",
        ],
        "watch": "Keep your back straight and your knees in line with your toes.",
        "camera": "Stand sideways to the camera so your whole body is visible.",
    },
    "Push-ups": {
        "steps": [
            "Place your hands under your shoulders and make a straight line from head to heels.",
            "Bend your elbows and lower your chest toward the floor.",
            "Stop when your elbows reach about 90 degrees.",
            "Push the floor away until your arms are straight.",
        ],
        "watch": "Don't let your hips sag or pike up.",
        "camera": "Place the camera at your side, low, so your whole body is in view.",
    },
    "Biceps Curls (Dumbbell)": {
        "steps": [
            "Stand tall with a dumbbell in your hand and your arm straight down.",
            "Keep your elbow pinned to your side.",
            "Curl the weight up by bending only your elbow.",
            "Lower it slowly until your arm is straight again.",
        ],
        "watch": "No swinging. Your elbow and torso should stay still.",
        "camera": "Stand sideways with the working arm facing the camera.",
    },
    "Shoulder Press": {
        "steps": [
            "Hold the dumbbells at shoulder height with your elbows bent.",
            "Brace your core and keep your ribs down.",
            "Press the weights straight up until your arms are extended.",
            "Lower them back to your shoulders with control.",
        ],
        "watch": "Don't arch your lower back as you press.",
        "camera": "Stand sideways to the camera, with your head to your hips in view.",
    },
    "Lunges": {
        "steps": [
            "Stand tall with your feet together.",
            "Step forward and lower your hips straight down.",
            "Stop when both knees are bent to about 90 degrees.",
            "Push through your front heel to return to standing.",
        ],
        "watch": "Keep your torso upright and your front knee over your ankle.",
        "camera": "Stand sideways to the camera so both legs are visible.",
    },
}



STAND = {
    "head": (140, 86), "shoulder": (140, 110), "hip": (140, 180),
    "knee": (140, 240), "ankle": (140, 300), "toe": (164, 304),
    "elbow": (146, 150), "wrist": (146, 190),
}


def _pose(**changes):
    return {**STAND, **changes}


POSES = {
    "Squats": {
        "start": _pose(elbow=(172, 110), wrist=(204, 110)),
        "end": _pose(head=(168, 167), shoulder=(159, 192), hip=(119, 249), knee=(179, 254),
                     elbow=(191, 192), wrist=(223, 192)),
        "weights": False,
    },
    "Push-ups": {
        "start": dict(head=(256, 214), shoulder=(232, 226), hip=(168, 255), knee=(114, 281),
                      ankle=(60, 302), toe=(64, 306), elbow=(232, 266), wrist=(232, 306)),
        "end": dict(head=(262, 270), shoulder=(236, 274), hip=(171, 284), knee=(116, 293),
                    ankle=(60, 302), toe=(64, 306), elbow=(206, 278), wrist=(232, 306)),
        "weights": False,
    },
    "Biceps Curls (Dumbbell)": {
        "start": _pose(),
        "end": _pose(wrist=(166, 117)),
        "weights": True,
    },
    "Shoulder Press": {
        "start": _pose(elbow=(150, 148), wrist=(150, 108)),
        "end": _pose(elbow=(164, 74), wrist=(172, 35)),
        "weights": True,
    },
    "Lunges": {
        "start": _pose(),
        "end": _pose(head=(148, 148), shoulder=(148, 172), hip=(148, 242), knee=(208, 242),
                     ankle=(196, 300), toe=(220, 304), elbow=(154, 212), wrist=(154, 252),
                     knee2=(116, 292), ankle2=(60, 286), toe2=(84, 304)),
        "weights": False,
    },
}

NEAR_LIMBS = [("shoulder", "hip"), ("hip", "knee"), ("knee", "ankle"), ("ankle", "toe"),
              ("shoulder", "elbow"), ("elbow", "wrist")]
FAR_LIMBS = [("hip", "knee2"), ("knee2", "ankle2"), ("ankle2", "toe2")]


def _with_far_leg(pose):
    """The far leg follows the near leg unless the pose gives it its own position."""
    return {"knee2": pose["knee"], "ankle2": pose["ankle"], "toe2": pose["toe"], **pose}


def _animate(attribute, start, end):
    if start == end:
        return ""
    return (
        f'<animate attributeName="{attribute}" values="{start};{start};{end};{end};{start}" '
        f'keyTimes="{KEY_TIMES}" keySplines="{KEY_SPLINES}" calcMode="spline" '
        f'dur="{LOOP_SECONDS}s" repeatCount="indefinite"/>'
    )


def _line(a, b, start, end, css_class):
    (x1, y1), (x2, y2) = start[a], start[b]
    animations = (
        _animate("x1", x1, end[a][0]) + _animate("y1", y1, end[a][1])
        + _animate("x2", x2, end[b][0]) + _animate("y2", y2, end[b][1])
    )
    return f'<line class="{css_class}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{animations}</line>'


def _circle(joint, start, end, radius, css_class):
    cx, cy = start[joint]
    animations = _animate("cx", cx, end[joint][0]) + _animate("cy", cy, end[joint][1])
    return f'<circle class="{css_class}" cx="{cx}" cy="{cy}" r="{radius}">{animations}</circle>'


@lru_cache(maxsize=None)
def _demo_html(exercise: str) -> str:
    spec = POSES[exercise]
    start, end = _with_far_leg(spec["start"]), _with_far_leg(spec["end"])

    shapes = [_line(a, b, start, end, "limb far") for a, b in FAR_LIMBS]
    shapes += [_line(a, b, start, end, "limb") for a, b in NEAR_LIMBS]
    shapes += [_circle("head", start, end, 15, "head")]
    shapes += [_circle(joint, start, end, 4, "joint") for joint in ("elbow", "knee", "hip")]
    if spec["weights"]:
        shapes.append(_circle("wrist", start, end, 9, "weight"))

    return f"""<!doctype html>
<html><head><style>
  html, body {{ margin: 0; height: 100%; background: #181D2A; }}
  .wrap {{ box-sizing: border-box; height: 100%; border: 1px solid rgba(255,255,255,.08);
           display: flex; align-items: center; justify-content: center; }}
  svg {{ width: 100%; height: 100%; }}
  .ground {{ stroke: rgba(255,255,255,.2); stroke-width: 2; }}
  .limb {{ stroke: #F5F7FA; stroke-width: 7; stroke-linecap: round; fill: none; }}
  .far {{ stroke: rgba(245,247,250,.35); }}
  .head {{ fill: none; stroke: #F5F7FA; stroke-width: 6; }}
  .joint {{ fill: #181D2A; stroke: #F5F7FA; stroke-width: 3; }}
  .weight {{ fill: #9AA4B2; stroke: #F5F7FA; stroke-width: 3; }}
  .label {{ fill: rgba(255,255,255,.5); font: 12px sans-serif; }}
</style></head><body><div class="wrap">
<svg viewBox="0 0 300 330" preserveAspectRatio="xMidYMid meet" role="img" aria-label="{exercise} demonstration">
  <line class="ground" x1="20" y1="309" x2="280" y2="309"/>
  {"".join(shapes)}
  <text class="label" x="150" y="326" text-anchor="middle">SIDE VIEW</text>
</svg></div></body></html>"""


def _custom_image(exercise: str):
    slug = re.sub(r"[^a-z0-9]+", "_", exercise.lower()).strip("_")
    for extension in IMAGE_EXTENSIONS:
        path = CUSTOM_IMAGE_DIR / f"{slug}.{extension}"
        if path.is_file():
            return path
    return None


def render_exercise_guide(exercise):
    """Show how to do the exercise: a looping demo, the steps and what to watch for."""
    guide = GUIDES.get(exercise)
    if not guide:
        return

    st.markdown(f"#### How to do it: {exercise}")

    image = _custom_image(exercise)
    if image:
        try:
            st.image(str(image), width="stretch")
        except Exception:
            st.image(str(image))
    else:
        components.html(_demo_html(exercise), height=DEMO_HEIGHT)

    st.markdown("\n".join(f"{i}. {step}" for i, step in enumerate(guide["steps"], start=1)))
    st.info(f"**Watch for:** {guide['watch']}")
    st.caption(f"📷 {guide['camera']}")