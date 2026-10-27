# Phase 6 Pattern Map

| New behavior | Existing analog | Reuse/constraint |
|---|---|---|
| Cards migration | lookup/store.py _v3/MIGRATIONS | Add guarded _v4; retain existing data and private paths |
| History snapshot | get_word_context | Read one word/translation/context/span/meaning/provider pair |
| Core learning | lookup/context.py and store helpers | Stdlib-only small functions, bound SQL, fixed errors |
| Native windows | lookup/gui.py components/PlainBlock/Owner | Lazy Qt, native palette/plain text, one reusable owned surface |
| Popup add | Owner.receive/Popup.result/update_context | Capture displayed accepted pair, never fetch a later mutable history value |
| Connection lifecycle | open_store and Engine._resources | Separate GUI-owned short-timeout connection; never cross threads |
| Qt tests | tests/test_app_gui.py | Offscreen actual widgets with throwaway store and fake engine |
| Target evidence | tools/check_context_app.py | Synthetic fixtures, owned process/profile, compact report and restoration |

Suggested exclusive ownership: core unit owns learning.py/store.py and core tests; GUI unit owns learning_gui.py/gui.py and widget tests; acceptance owns tools/check_learning_app.py and harness tests. Later fixes follow same ownership. No new runtime dependency.
