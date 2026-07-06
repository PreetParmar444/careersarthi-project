"""
careersarthi/utils/pii_redactor.py
────────────────────────────────────
Strips PII (email, phone, Aadhaar, PAN, salary expectations, home address)
from any text before it is sent to an external LLM API call.
All redaction happens locally — no data leaves until this layer clears it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import NamedTuple


# ── Pattern registry ──────────────────────────────────────────────────────────

class _Pattern(NamedTuple):
    label: str
    regex: str
    replacement: str


_PATTERNS: list[_Pattern] = [
    _Pattern("EMAIL",     r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", "[EMAIL]"),
    _Pattern("PHONE_IN",  r"(?:\+91[\-\s]?)?[6-9]\d{9}", "[PHONE]"),
    _Pattern("PHONE_INT", r"\+?[1-9]\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{4}", "[PHONE]"),
    _Pattern("AADHAAR",   r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b", "[AADHAAR]"),
    _Pattern("PAN",       r"\b[A-Z]{5}\d{4}[A-Z]\b", "[PAN]"),
    _Pattern("SALARY",    r"(?:CTC|salary|package|LPA|lpa|lakhs?|₹|INR)\s*[:\-]?\s*\d+[\d,.]*(?:\s*(?:lakh|lac|L|k|K|cr)?)?", "[SALARY]"),
    _Pattern("ADDRESS",   r"\b\d{1,5}[,\s]+(?:[A-Za-z\s]+,\s*){1,3}(?:Mumbai|Delhi|Bangalore|Bengaluru|Chennai|Hyderabad|Pune|Ahmedabad|Kolkata|Jaipur|Lucknow|Surat|Vadodara|Noida|Gurgaon|Gurugram)\b", "[ADDRESS]"),
    _Pattern("PINCODE",   r"\b[1-9][0-9]{5}\b", "[PINCODE]"),
    _Pattern("DOB",       r"\b(?:\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}|\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})\b", "[DOB]"),
    _Pattern("LINKEDIN",  r"linkedin\.com/in/[a-zA-Z0-9\-_%]+", "[LINKEDIN_URL]"),
    _Pattern("GITHUB",    r"github\.com/[a-zA-Z0-9\-_%]+", "[GITHUB_URL]"),
]

_COMPILED = [(p.label, re.compile(p.regex, re.IGNORECASE), p.replacement) for p in _PATTERNS]


# ── Result type ───────────────────────────────────────────────────────────────

@dataclass
class RedactionResult:
    clean_text: str
    redacted_items: dict[str, list[str]] = field(default_factory=dict)

    @property
    def redaction_count(self) -> int:
        return sum(len(v) for v in self.redacted_items.values())

    @property
    def was_redacted(self) -> bool:
        return self.redaction_count > 0


# ── Public API ────────────────────────────────────────────────────────────────

def redact(text: str) -> RedactionResult:
    """
    Redact all recognised PII from *text*.

    Returns a :class:`RedactionResult` with the cleaned text and a log
    of what was found (values replaced, not the originals — we don't keep PII
    even in the log).
    """
    result = text
    found: dict[str, list[str]] = {}

    for label, pattern, replacement in _COMPILED:
        matches = pattern.findall(result)
        if matches:
            found[label] = [replacement] * len(matches)   # log count, not value
            result = pattern.sub(replacement, result)

    return RedactionResult(clean_text=result, redacted_items=found)


def is_safe(text: str) -> bool:
    """Quick check — returns True only if no PII is detected."""
    return not redact(text).was_redacted


# ── CLI helper (python -m careersarthi.utils.pii_redactor "some text") ───────
if __name__ == "__main__":
    import sys
    sample = " ".join(sys.argv[1:]) or "Call me at +91 98765 43210 or rahul.sharma@gmail.com"
    res = redact(sample)
    print("Clean :", res.clean_text)
    print("Found :", res.redacted_items)
