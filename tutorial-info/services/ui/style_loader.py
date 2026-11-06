import base64
import json
import os
from functools import lru_cache
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


DEFAULT_FONT_PATH = str(Path(__file__).resolve().parents[2] / "static" / "AdobeClean.otf")
DEFAULT_FONT_NAME = "AdobeClean"

# extension -> (mime type, css format)
FONT_TYPES = {
    "otf": ("font/otf", "opentype"),
    "ttf": ("font/ttf", "truetype"),
    "woff": ("font/woff", "woff"),
    "woff2": ("font/woff2", "woff2"),
}


@lru_cache(maxsize=None)
def _font_face_css(font_path: str, font_name: str) -> str:
    """Build the @font-face rule once. Returns "" if the font file is missing."""
    if not os.path.exists(font_path):
        return ""

    ext = os.path.splitext(font_path)[1].lstrip(".").lower()
    mime, fmt = FONT_TYPES.get(ext, (f"font/{ext}", ext))

    with open(font_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    return (
        f"@font-face {{"
        f"font-family: '{font_name}';"
        f"src: url('data:{mime};base64,{encoded}') format('{fmt}');"
        f"font-weight: 100 900;"
        f"font-style: normal;"
        f"}}"
    )


def load_css(file_path: str):
    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def inject_local_font(font_path: str, font_name: str):
    css = _font_face_css(font_path, font_name)
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


_WEBRTC_JS = """
<script>
(function () {
    const css = __CSS__;

    function patch() {
        try {
            window.parent.document.querySelectorAll('iframe').forEach(function (iframe) {
                if (!iframe.src || iframe.src.indexOf('webrtc') === -1) return;

                const doc = iframe.contentDocument;
                if (!doc || !doc.head || doc.getElementById('webrtc-custom-styles')) return;

                const style = doc.createElement('style');
                style.id = 'webrtc-custom-styles';
                style.textContent = css;
                doc.head.appendChild(style);
            });
        } catch (e) {
            console.warn('WebRTC style patch failed:', e);
        }
    }

    // The WebRTC iframe may not exist yet, so keep retrying
    patch();
    setInterval(patch, 1000);
})();
</script>
"""


def inject_webrtc_styles(font_path: str = DEFAULT_FONT_PATH, font_name: str = DEFAULT_FONT_NAME):
    """Style the streamlit-webrtc buttons (they live inside their own iframe)."""
    css = _font_face_css(font_path, font_name) + f"""
        .MuiButtonBase-root,
        .MuiButton-root,
        .MuiButton-contained,
        .MuiButton-text {{
            border-radius: 0 !important;
            font-family: '{font_name}', sans-serif !important;
            letter-spacing: 0.05em !important;
        }}
        /* Hide the "Video Input" device picker; the default camera is used */
        .MuiFormControl-root {{
            display: none !important;
        }}
    """

    components.html(_WEBRTC_JS.replace("__CSS__", json.dumps(css)), height=0)