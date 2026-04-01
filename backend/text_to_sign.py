"""
Text-to-sign translation with video asset discovery.

Maps common English words/phrases to ASL-style gloss labels and fingerspells
unknown tokens. Finds and includes video URLs for each sign. Returns a 
structured sign sequence with media paths for the frontend.
"""

from __future__ import annotations

import os
import string
from typing import Any

from notebook_text_to_sign_adapter import run_notebook_text_to_sign

_PUNCT = str.maketrans("", "", string.punctuation.replace("'", ""))

# Multi-word phrases first (longest match applied by scanning joined text)
_PHRASE_GLOSSES: list[tuple[str, list[str]]] = [
    ("thank you", ["THANK-YOU"]),
    ("good morning", ["GOOD", "MORNING"]),
    ("good afternoon", ["GOOD-AFTERNOON"]),
    ("good night", ["GOOD", "NIGHT"]),
    ("how are you", ["HOW", "YOU"]),
    ("see you later", ["SEE", "LATER"]),
    ("excuse me", ["EXCUSE", "ME"]),
    ("i love you", ["I", "LOVE", "YOU"]),
]
_PHRASE_GLOSSES.sort(key=lambda item: len(item[0].split()), reverse=True)

# Single-word lexical glosses (lowercase keys)
_LEXICON: dict[str, str] = {
    "hello": "HELLO",
    "hi": "HELLO",
    "hey": "HELLO",
    "yes": "YES",
    "no": "NO",
    "please": "PLEASE",
    "sorry": "SORRY",
    "help": "HELP",
    "thanks": "THANK-YOU",
    "thank": "THANK-YOU",
    "deaf": "DEAF",
    "hearing": "HEARING",
    "learn": "LEARN",
    "sign": "SIGN",
    "language": "LANGUAGE",
    "good": "GOOD",
    "bad": "BAD",
    "morning": "MORNING",
    "afternoon": "AFTERNOON",
    "night": "NIGHT",
    "bye": "BYE",
    "goodbye": "BYE",
    "water": "WATER",
    "food": "FOOD",
    "eat": "EAT",
    "drink": "DRINK",
    "friend": "FRIEND",
    "family": "FAMILY",
    "name": "NAME",
    "my": "MY",
    "your": "YOUR",
    "i": "I",
    "you": "YOU",
    "we": "WE",
    "they": "THEY",
    "what": "WHAT",
    "where": "WHERE",
    "when": "WHEN",
    "why": "WHY",
    "how": "HOW",
    "who": "WHO",
    "love": "LOVE",
}


def _normalize_words(text: str) -> list[str]:
    t = text.lower().strip()
    t = t.translate(_PUNCT)
    return [w for w in t.split() if w]


def _fingerspell(token: str) -> list[str]:
    return [c.upper() for c in token.lower() if c.isalpha()]


def _get_signs_dir() -> str:
    """Get the absolute path to the static/signs directory."""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(backend_dir)
    return os.path.join(project_dir, "static", "signs")


def _find_video_url(gloss: str, english: str = "") -> str | None:
    """
    Find a video file for a sign and return its URL path.
    
    Args:
        gloss: The sign gloss (e.g., "HELLO", "THANK-YOU")
        english: The English word (e.g., "hello", "thank you")
    
    Returns:
        URL path like "/static/signs/hello.mp4" or None if not found
    """
    signs_dir = _get_signs_dir()
    if not os.path.isdir(signs_dir):
        return None
    
    # Generate candidate filenames to check
    candidates = []
    
    # Based on gloss
    if gloss:
        candidates.append(gloss.lower())
        candidates.append(gloss.lower().replace("_", "-"))
        candidates.append(gloss.upper())
    
    # Based on english word
    if english:
        candidates.append(english.lower())
        candidates.append(english.lower().replace(" ", "-"))
        candidates.append(english.lower().replace(" ", "_"))
    
    # Remove duplicates while preserving order
    candidates = list(dict.fromkeys(candidates))
    
    # Check for video/image files with various extensions
    extensions = ["mp4", "webm", "gif", "png", "jpg", "jpeg", "avi", "mov"]
    
    for candidate in candidates:
        for ext in extensions:
            filepath = os.path.join(signs_dir, f"{candidate}.{ext}")
            if os.path.isfile(filepath):
                # Return relative URL path
                return f"/static/signs/{candidate}.{ext}"
    
    return None


def _gloss_for_word(word: str) -> list[dict[str, Any]]:
    if not word:
        return []
    if word in _LEXICON:
        g = _LEXICON[word]
        video_url = _find_video_url(g, word)
        return [
            {
                "kind": "lexical",
                "gloss": g,
                "english": word,
                "video_url": video_url,
            }
        ]
    letters = _fingerspell(word)
    if not letters:
        return [{"kind": "literal", "text": word}]
    return [
        {
            "kind": "fingerspell",
            "letters": letters,
            "english": word,
        }
    ]


def _process_text_to_sign_fallback(text: str) -> dict[str, Any]:
    """
    Convert user text into an ordered sign representation (glosses + fingerspelling).

    Returns:
        success: bool
        original: str
        gloss_line: str — space-separated gloss labels for display
        sign_sequence: list of step objects (lexical | fingerspell | literal)
        summary: short description for status messages
    """
    raw = (text or "").strip()
    if not raw:
        return {"success": False, "message": "No text provided"}

    words = _normalize_words(raw)
    if not words:
        return {"success": False, "message": "No usable words after normalization"}

    sequence: list[dict[str, Any]] = []
    gloss_tokens: list[str] = []
    i = 0
    n = len(words)

    while i < n:
        matched = False
        for phrase, glosses in _PHRASE_GLOSSES:
            pw = phrase.split()
            if i + len(pw) > n:
                continue
            if words[i : i + len(pw)] == pw:
                phrase_english = " ".join(pw)
                for g in glosses:
                    video_url = _find_video_url(g, phrase_english)
                    sequence.append(
                        {
                            "kind": "lexical",
                            "gloss": g,
                            "english": phrase_english,
                            "video_url": video_url,
                        }
                    )
                    gloss_tokens.append(g)
                i += len(pw)
                matched = True
                break
        if matched:
            continue

        w = words[i]
        parts = _gloss_for_word(w)
        for p in parts:
            sequence.append(p)
            if p["kind"] == "lexical":
                gloss_tokens.append(p["gloss"])
            elif p["kind"] == "fingerspell":
                gloss_tokens.append("-".join(p["letters"]))
            elif p["kind"] == "literal":
                gloss_tokens.append(p.get("text", ""))
        i += 1

    gloss_line = " ".join(g for g in gloss_tokens if g).strip()
    summary = f"{len(sequence)} sign unit(s) generated from {len(words)} word(s)."

    return {
        "success": True,
        "original": raw,
        "gloss_line": gloss_line,
        "sign_sequence": sequence,
        "summary": summary,
    }


def process_text_to_sign(text: str) -> dict[str, Any]:
    # Prefer notebook-backed implementation when available.
    notebook_result = run_notebook_text_to_sign(text)
    if isinstance(notebook_result, dict) and notebook_result:
        notebook_result.setdefault("success", True)
        return notebook_result

    return _process_text_to_sign_fallback(text)
