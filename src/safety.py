import re


class SafetyChecker:
    FINAL_WORK_PATTERNS = [
        r"\bwrite (the )?(whole|entire|final)\b",
        r"\bdo (it|this|my assignment) for me\b",
        r"\bsubmit\b.*\bfor me\b",
        r"\bcopy[- ]?paste\b",
        r"\bfull answer\b",
        r"\bfinal deliverable\b",
    ]

    OFF_TOPIC_PATTERNS = [
        r"\bweather\b",
        r"\bstock price\b",
        r"\bmovie\b",
        r"\bfootball\b",
    ]

    PROMPT_EXTRACTION_PATTERNS = [
        r"\bsystem prompt\b",
        r"\bhidden instructions?\b",
        r"\bsupervisor logic\b",
        r"\bdeveloper message\b",
        r"\bignore (all )?(previous|prior) instructions\b",
    ]

    def check(self, message: str) -> dict[str, bool]:
        normalized = message.lower()
        asks_final_work = any(re.search(pattern, normalized) for pattern in self.FINAL_WORK_PATTERNS)
        off_topic = any(re.search(pattern, normalized) for pattern in self.OFF_TOPIC_PATTERNS)
        prompt_extraction = any(re.search(pattern, normalized) for pattern in self.PROMPT_EXTRACTION_PATTERNS)
        return {
            "asks_final_work": asks_final_work,
            "off_topic": off_topic,
            "prompt_extraction": prompt_extraction,
            "needs_redirect": asks_final_work or off_topic or prompt_extraction,
        }
