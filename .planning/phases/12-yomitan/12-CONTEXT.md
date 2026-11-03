# Phase 12: Yomitan dictionaries

## Decisions (agent-selected under --auto)
- Use the supplied `D:/User/Downloads/English-Russian_dict_Yomitan.zip` as the real acceptance archive. Do not commit third-party dictionary content.
- Keep existing folder/settings workflow: copy ZIP without extraction, apply settings; replace the same filename to reconnect. Existing IDs, ordering, disabled state and failure isolation remain authoritative.
- Support v3 term banks, including plain text and structured content, as safe plain-text articles. No remote resource loading or archive extraction.
- Invalid, oversized and unsupported archives use existing dictionary diagnostics. One broken archive must not disable other dictionaries.
- Record agent testing as agent testing, not human feedback. Other archives/format versions remain unverified.

## Scope
DICT-04, DICT-05; no new import wizard or format conversion dependency.
