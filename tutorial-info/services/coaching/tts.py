
import logging
from io import BytesIO

from gtts import gTTS

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_S = 10


class TextToSpeech:
    def __init__(self, lang="en", slow=False):
        self.lang = lang
        self.slow = slow

    def speak(self, text, lang=None):
        """Return MP3 bytes for the text, or None if it is empty or conversion fails."""
        cleaned = (text or "").strip()
        if not cleaned:
            return None

        try:
            buffer = BytesIO()
            
            gTTS(
                text=cleaned,
                lang=lang or self.lang,
                slow=self.slow,
                timeout=REQUEST_TIMEOUT_S,
            ).write_to_fp(buffer)
            return buffer.getvalue()
        except Exception:
            logger.exception("Text-to-speech failed")
            return None