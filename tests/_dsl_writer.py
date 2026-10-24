"""Test-only Lingvo DSL writer for the DSL reader tests (stdlib only).

write_dsl() lays a dictionary out the way ABBYY Lingvo does: a header of `#KEY "value"`
lines, then per article one or more unindented headword lines followed by indented body
lines. Any of the common encodings can be produced, with or without a byte-order mark,
and the result can be wrapped as dictzip (.dsl.dz) with make_dictzip().
"""
from pathlib import Path

from tests._dictzip_writer import make_dictzip

_BOMS = {"utf-16-le": b"\xff\xfe", "utf-16-be": b"\xfe\xff", "utf-8": b"\xef\xbb\xbf"}
_CODECS = {"utf-16": "utf-16-le", "utf-16-le": "utf-16-le", "utf-16-be": "utf-16-be", "utf-8": "utf-8"}


def write_dsl(
    path,
    entries,
    *,
    name="Test",
    encoding="utf-16",
    bom=True,
    newline="\r\n",
    index_language="English",
    contents_language="Russian",
    dz=False,
    chunk_len=4096,
) -> Path:
    """Write `entries` (a list of (headwords, body_lines)) to `path` and return the real path.

    "utf-16" means little endian, as Lingvo writes it. Body lines that do not already start
    with a space or a tab get one space of indentation; an empty line stays empty. With
    dz=True the file is dictzip-compressed and gets a ".dz" suffix (the returned path).
    A name of None leaves the #NAME line out.
    """
    codec = _CODECS[encoding]
    lines = []
    if name is not None:
        lines.append('#NAME "%s"' % name)
    if index_language is not None:
        lines.append('#INDEX_LANGUAGE "%s"' % index_language)
    if contents_language is not None:
        lines.append('#CONTENTS_LANGUAGE "%s"' % contents_language)
    lines.append("")
    for headwords, body in entries:
        if isinstance(headwords, str):
            headwords = [headwords]
        lines.extend(headwords)
        for line in body:
            lines.append(line if not line or line[0] in " \t" else " " + line)
    text = "".join(line + newline for line in lines)
    raw = (_BOMS[codec] if bom else b"") + text.encode(codec)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if dz:
        path = path.with_name(path.name + ".dz")
        raw = make_dictzip(raw, chunk_len=chunk_len, fname=path.name[:-3])
    path.write_bytes(raw)
    return path
