
import logging
from collections import deque

from openai import OpenAI

from services.config.workout_config import PROMPT

logger = logging.getLogger(__name__)

MODEL = "gpt-4o-mini"
HISTORY_MESSAGES = 10     
REQUEST_TIMEOUT_S = 8


class LLMCoach:
    def __init__(self, openai_client=None):
        
        client = openai_client or OpenAI()
        self.client = client.with_options(timeout=REQUEST_TIMEOUT_S, max_retries=1)
        self.model = MODEL
        self.history = deque(maxlen=HISTORY_MESSAGES)

    def give_feedback(self, event, issue=None):
        """Return a short spoken coaching cue, or None if none could be generated."""
        prompt = f"Event: {event}"
        if issue:
            prompt += f"\nForm Issue: {issue}"

        messages = [
            {"role": "system", "content": PROMPT},
            *self.history,
            {"role": "user", "content": prompt},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.4,
                max_tokens=60, 
            )
        except Exception:
            logger.exception("OpenAI request failed")
            return None

        feedback = (response.choices[0].message.content or "").strip()
        if not feedback:
            return None

        self.history.append({"role": "user", "content": prompt})
        self.history.append({"role": "assistant", "content": feedback})
        return feedback