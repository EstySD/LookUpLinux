"""Counting-key normalisation for looked-up words and short phrases (DATA-02)."""
import unicodedata as ud

# Explicit maps run BEFORE NFKC: NFKC does not fold these to ASCII
# (U+2019, U+02BC stay; U+00B4 becomes " ́").
_APOS = dict.fromkeys(map(ord, "‘’‚‛ʼ′´`"), "'")
_DQUO = dict.fromkeys(map(ord, "“”„‟«»″‹›\""), '"')
_DASH = dict.fromkeys(map(ord, "‐‑‒–—−"), "-")
_INNER_OK = frozenset("'-")

# Contractions where "'s" is not a possessive and must be kept (D-16).
CONTRACTIONS = frozenset(
    {
        "it's", "let's", "that's", "what's", "he's", "she's",
        "there's", "here's", "who's", "where's", "how's",
    }
)


def _strip_edges(w: str) -> str:
    i, j = 0, len(w)
    while i < j and not w[i].isalpha():
        i += 1
    while j > i and not w[j - 1].isalpha():
        j -= 1
    return w[i:j]


def normalize(text: str) -> str | None:
    """Return the counting key for a word or 1-N word phrase, or None to reject.

    The caller must not touch the database when None is returned (D-04).
    """
    if not isinstance(text, str):
        raise TypeError("text must be str, got " + type(text).__name__)
    t = text.translate(_APOS).translate(_DQUO).translate(_DASH)
    t = ud.normalize("NFKC", t)                              # ligatures, fullwidth, nbsp, Kelvin
    t = "".join(c for c in t if ud.category(c) != "Cf")      # soft hyphen, ZWSP, BOM
    t = ud.normalize("NFC", t.casefold())
    t = "".join(c for c in t if ud.category(c) != "Mn")      # stray combining marks
    tokens = t.split()
    if not tokens:
        return None
    out = []
    for raw in tokens:
        if any(c.isnumeric() for c in raw):                  # D-17: before edge trimming
            return None
        w, prev = _strip_edges(raw), None
        while w != prev:                                     # fixed point -> idempotent
            prev = w
            if w in CONTRACTIONS:
                break
            if w.endswith("'s") and len(w) > 2:
                w = w[:-2]
            w = _strip_edges(w)
        if not w:
            return None
        for c in w:
            if c in _INNER_OK:
                continue
            if not c.isalpha():                              # punctuation inside token
                return None
            if not ud.name(c, "").startswith("LATIN"):       # Cyrillic, mixed script, CJK
                return None
        out.append(w)
    key = " ".join(out)
    if len(key) < 2 and key not in ("a", "i"):
        return None
    return key
