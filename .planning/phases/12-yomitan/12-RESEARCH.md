# Archive and integration research

Supplied archive: 3,674,469 bytes; root index.json declares format 3, title English-Russian_dict, revision 1.0, language en. Two term banks contain 48,523 eight-field rows. Definitions use structured-content with nested div/span nodes and styles. Russian text is intact (console rendering must not be mistaken for source corruption).

Existing integration: dicts.discover -> open_all -> DictSet.find -> translate.lookup; settings folder and apply reload already reconnect readers. Add ZIP discovery, one reader and doctor probe. Preserve source files and atomically publish only a fully parsed reader. Enforce compressed/uncompressed/member/bank/entry/depth limits; never extract files or interpret CSS/URLs.

Known limit: cold loading parses JSON banks in memory; measure real load and bounded doctor timeout. Multimedia is omitted, not fetched. Only v3 is claimed.
