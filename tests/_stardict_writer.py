"""Test-only StarDict writer for every supported layout (stdlib plus _dictzip_writer).

write_stardict() builds a real StarDict dictionary on disk. `entries` is a list of
(headword, data); data is bytes (the raw field layout, written as given) or str
(UTF-8). With sametypesequence set the caller supplies the fields concatenated as
the format requires; without it the caller supplies the type-byte layout. The
writer never validates, so tests can build deliberately broken dictionaries
(wordcount that disagrees, 64-bit offsets with an old version, raw extra index
records such as the Mueller 7 entry with an empty headword and a huge size).
"""
import gzip
import struct
from pathlib import Path

from tests._dictzip_writer import make_dictzip


def _raw(data) -> bytes:
    return data.encode("utf-8") if isinstance(data, str) else bytes(data)


def write_stardict(
    directory,
    stem,
    entries,
    *,
    bookname=None,
    sametypesequence="m",
    dz=False,
    plain_dict=True,
    gz_idx=False,
    offset_bits=32,
    version="2.4.2",
    syn=None,
    extra_idx=None,
    wordcount=None,
    dz_chunk_len=512,
) -> Path:
    """Write <stem>.ifo/.idx(.gz)/.dict(.dz)[/.syn] into `directory`; return the .ifo path.

    extra_idx: raw index records (headword_bytes, offset, size) appended after the
    normal entries. syn: list of (word, entry_number). wordcount overrides the
    (otherwise correct) value written to the .ifo.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    offset_pack = ">Q" if offset_bits == 64 else ">I"

    data = bytearray()
    idx = bytearray()
    for word, payload in entries:
        raw = _raw(payload)
        idx += _raw(word) + b"\x00" + struct.pack(offset_pack, len(data)) + struct.pack(">I", len(raw))
        data += raw
    for word, offset, size in extra_idx or ():
        idx += bytes(word) + b"\x00" + struct.pack(offset_pack, offset) + struct.pack(">I", size)

    idx_bytes = gzip.compress(bytes(idx)) if gz_idx else bytes(idx)
    (directory / (stem + (".idx.gz" if gz_idx else ".idx"))).write_bytes(idx_bytes)
    if plain_dict:
        (directory / (stem + ".dict")).write_bytes(bytes(data))
    if dz:
        (directory / (stem + ".dict.dz")).write_bytes(make_dictzip(bytes(data), chunk_len=dz_chunk_len))
    if syn is not None:
        blob = b"".join(_raw(w) + b"\x00" + struct.pack(">I", n) for w, n in syn)
        (directory / (stem + ".syn")).write_bytes(blob)

    lines = [
        "StarDict's dict ifo file",
        "version=" + version,
        "bookname=" + (stem if bookname is None else bookname),
        "wordcount=" + str(len(entries) if wordcount is None else wordcount),
        "idxfilesize=" + str(len(idx)),
    ]
    if offset_bits != 32:
        lines.append("idxoffsetbits=" + str(offset_bits))
    if sametypesequence is not None:
        lines.append("sametypesequence=" + sametypesequence)
    ifo = directory / (stem + ".ifo")
    ifo.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    return ifo
