"""Slug generation.

A slug goes in a URL, so it has to survive names that are not ASCII — the
product ships in Ukrainian, and "Компанія" must produce something addressable
rather than an empty string.
"""

from __future__ import annotations

import re
import secrets
import unicodedata

MAX_LENGTH = 60
# Latin transliteration for Cyrillic. `unicodedata` decomposition strips accents
# from Latin letters but leaves Cyrillic untouched, so it needs its own table.
CYRILLIC = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "h",
    "ґ": "g",
    "д": "d",
    "е": "e",
    "є": "ie",
    "ж": "zh",
    "з": "z",
    "и": "y",
    "і": "i",
    "ї": "i",
    "й": "i",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ь": "",
    "ю": "iu",
    "я": "ia",
    "ы": "y",
    "э": "e",
    "ё": "e",
    "ъ": "",
}


def slugify(name: str) -> str:
    """A URL-safe slug, or an empty string if nothing survives.

    The caller decides what to do with an empty result — this does not invent a
    name, because a silently invented one is worse than a rejected input.
    """
    lowered = name.strip().lower()
    transliterated = "".join(CYRILLIC.get(char, char) for char in lowered)
    # Decompose, then drop combining marks: "Café" becomes "cafe".
    decomposed = unicodedata.normalize("NFKD", transliterated)
    ascii_only = decomposed.encode("ascii", "ignore").decode("ascii")

    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")
    return slug[:MAX_LENGTH].rstrip("-")


def unique_suffix() -> str:
    """Four hex characters, for when a slug is already taken.

    Not a counter: counting requires a query per attempt and tells anyone reading
    the URL how many organisations share a name.
    """
    return secrets.token_hex(2)
