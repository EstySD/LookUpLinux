# Phase 8 GAME-01 gap: bounded remedy research

**Date:** 2026-10-31. **Result:** Recommend one bounded AssaultCube pilot, retaining failed Doom evidence. **Confidence:** HIGH for downloaded provenance/source behavior; MEDIUM for likelihood of readable text; renderer/OCR/actual routes remain unverified.

## User Constraints

[VERIFIED: 08-CONTEXT.md and 08-VERIFICATION.md, commit 1a6b6f3] Preserve all locked D-01..D-10: owned clone/account only, no original VM mutation, no lowered performance/game criteria, unchanged source capture/OCR/Query, actual physical input and useful compositor-visible overlay, dismissal then real camera/movement, explicit cleanup and agent acceptance. Research owns this new file only; existing 08-RESEARCH.md and user changes remain untouched. No VM boot/game mutation occurred.

[VERIFIED: canonical docs/lookupper/architecture.md, linux-requirements.md, evidence.md and 08-04-SUMMARY.md] Original claims are not Linux proof. Wesnoth already supplies two accepted routes in **one** game. The missing condition is useful OCR while a real second fullscreen game has captured relative mouse, followed by observed returned control. Changing the agent-selected game is permitted; removing that condition is not. Historical Phase7 strict false/original-disk unknown-actor exception remains separate and cannot waive GAME-01.

## Comparison and Recommendation

| Path | Evidence now | Cost/risk | Decision |
| --- | --- | --- | --- |
| A: small general production OCR correction on saved Doom sources | Actual QUIT/HEALTH source/diagnostic retained; default preprocessing and alternative PSM diagnostics fail to produce a selected Query. | Could require new segmentation/color handling with broad accuracy/performance consequences; no demonstrated small fix yet. | Keep as bounded fallback, not the next implementation commitment. |
| B: AssaultCube actual local map + scoreboard | Official 52MB Linux package verified; included SDL2 client/source; authentic plain English score headings; source retains mouse grab based on focus/fullscreen rather than scoreboard visibility. | Requires functioning compatibility OpenGL under llvmpipe and a native readable-text pilot. | **Recommended first**: establish those prerequisites before extending acceptance harnesses. |

### Why A is not a confidence-threshold fix

[VERIFIED: lookup/ocr.py:_prepare_image/recognize_image and saved original diagnostics] Existing preprocessing takes a cursor-centered strip up to4096x256, flattens/inverts from background sampling, smoothly enlarges2x and adds an8px border; Tesseract6 output is transformed back before bounded selection. QUIT cursor670,440 falls on decorative red text over a textured world; matching glyphs are garbled. HEALTH cursor312,778 has no matching token; unrelated ARMOR appears at18.9 confidence. The saved QUIT image was visually inspected in this research. Lowering confidence cannot reconstruct absent/wrong glyphs and risks selecting unrelated text.

[VERIFIED: 08-04-SUMMARY] Aspect/integer/nearest/gamma variants already failed; EXIT navigation hit an actual vanilla visplane limit. Do not repeat a long Doom navigation campaign. A genuine future fallback could test a **general**, bounded alternate contrast/foreground preprocessing only after ordinary OCR yields no selection; it must improve the unchanged saved source at the actual cursor, preserve context/coordinate transforms and pass existing negative/noise corpus. Color-specific hardcoded word recognition, wider nearest-word selection, query replacement or bitmap/text substitution is not an acceptable correction. No such fix was demonstrated here; host Tesseract was not found by command/common-path probe, so no new OCR success is claimed.

## Verified AssaultCube Acquisition and Licensing

[VERIFIED: official release API plus downloaded archive2026-10-31] Official site https://assault.cubers.net/download.html links the Linux asset below from tagged release v1.3.0.2:

```text
https://github.com/assaultcube/AC/releases/download/v1.3.0.2/AssaultCube_v1.3.0.2_LockdownEdition_RC1.tar.bz2
bytes: 52071427
SHA256: 9b3118e7929253f0114fa06cad8310faab646d177b4660406011152f34086b55
```

The RC1 filename is the actual official Linux release asset, not an invented final filename. GitHub API returned no asset digest; the SHA above was computed independently over the downloaded bytes and is a reproducibility pin, not an independently signed upstream checksum. Download/extract only into the owned game directory, preserve archive hash and package version evidence. [VERIFIED: release metadata/download]

[VERIFIED: official Arch APIs] Direct Extra/x86_64 assaultcube endpoint returns404 and official package search returns zero results today. **Do not prescribe pacman -S assaultcube or a hidden AUR prerequisite.** Official archive includes `./bin_unix/linux_64_client`, server, source, configs and assets. ELF strings explicitly reference libSDL2-2.0.so.0, libSDL2_image-2.0.so.0 and libGL.so.1. Official download page still lists SDL1.2-era dependencies; use the actual archive's SDL2 binary/ldd result instead of copying that stale list.

[VERIFIED: archive docs/license.html and docs/package_copyrights.txt presence; CITED: official project README] The source is described as zlib-like; full package/assets have specific individual copyright/license terms. Preserve the complete unmodified game package and its license files for local testing; do not label every asset GPL/zlib or bundle it into LookUpLinux. No paid account or proprietary Doom data is needed. No redistribution licensing clearance is asserted.

## Exact Candidate Scene and Runtime Preconditions

[VERIFIED: included source/src/main.cpp and source/src/scoreboard.cpp; matching official tag sources] The client parses `-t1` for fullscreen, `-w1280 -h800`, `--home=PATH`, `--loadmap=ac_desert` and `-eCOMMAND`. Defaults select the built-in `default` font. Its shipped `config/font_default.cfg` uses `packages/misc/chars_default.png` with64px source glyph cells, unlike Doom's low-resolution decorative prompt; this is promising **not an OCR accuracy guarantee**. Do not modify font assets or insert fabricated English strings.

Suggested pilot command, run as the existing guarded owned graphical account, from the extracted game root (paths below are deliberate owned-test locations):

```sh
env SDL_VIDEODRIVER=wayland LIBGL_ALWAYS_SOFTWARE=true \
  WAYLAND_DEBUG=1 LD_PRELOAD=/absolute/path/to/owned/sdl-observer.so \
  ./bin_unix/linux_64_client \
  --home=/home/lookup07/.local/state/lookup-games-08/assaultcube/profile \
  --init -t1 -w1280 -h800 --loadmap=ac_desert
```

Use the current observer's real validated absolute path, not that example placeholder. First run `ldd` on this exact binary; install only actually missing official-repository runtime libraries, and record their versions. SDL2 compatibility, Mesa/OpenGL and OpenAL linkage are environment gates; the archive inspection did not prove they are all present on the powered-off VM. Avoid the launcher script's default home path; direct binary preserves isolated profile. Do not connect multiplayer/master server, use local map/offline session. If startup network chatter is observed, constrain only this owned game process/account without disrupting SSH/session services. [VERIFIED: binary/source/script inspection; selected pilot design]

[CITED: Mesa environment documentation; AssaultCube rendergl.cpp] `LIBGL_ALWAYS_SOFTWARE=true` requests software rendering; it does not prove successful llvmpipe. Require actual game's `Renderer:`/`Driver:` startup output, current PID/start/executable and KWin fullscreen/window geometry. SDL OpenGL compatibility context may still fail with the owned VM3D disabled: no fake renderer string, no assumption that VMSVGA flags establish rendering. Do not restore original VM or globally change KWin security/focus policy.

### Authentic word under actual mouse grab

1. Load the shipped `ac_desert` local map and physically walk/turn before testing. Open its actual scoreboard through supported `showscores 1`/normal game control; `showscores` calls `showmenu("score",false)`. Source-defined columns include **`deaths`**, **`name`**, `frags`, `ratio`. Prefer `deaths` or `name`, words available to the real dictionary, not a synthetic player name or injected console echo. The scoreboard is drawn by the game over an actual map, not a separate test UI. [VERIFIED: included scoreboard.cpp]
2. Inspect the actual frame and real KWin cursor coordinate. Use the already demonstrated desktop-toggle/preposition/refocus technique to put that cursor inside the genuine chosen heading, then reacquire game focus. Verify it remains there while grabbed; do not assume coordinates or select unrelated text. First do one physical product lookup with unchanged Source/real OCR and stop on correlated stage6. [VERIFIED: prior Doom preposition evidence; selected method]
3. **Require real grab proof for that same PID/start at the lookup:** source `inputgrab(true)` hides cursor, calls SDL_SetRelativeMouseMode(SDL_TRUE) and SDL_SetWindowGrab; fullscreen initialization and focus govern grab, and scoreboard code does not release it. This is source support only. Observe actual recent protocol locked state through the existing SDL/Wayland observer, with no intervening unlock before input; an open scoreboard must not be accepted if the runtime releases lock. [VERIFIED: included main.cpp/menus.cpp/scoreboard.cpp]
4. After actual useful overlay, physically dismiss it; require game focus and subsequent separate camera-motion and movement-key input/frame proofs. If scoreboard remains visible, close it with its real control before camera/movement, recording that transition after overlay dismissal. Do not reuse earlier control frames or count mere animation/FPS change as movement. [VERIFIED: current captured oracle contract]
5. Repeat from a changed map/camera position or second supported map, target the same genuine heading or a second real heading. Preserve distinct source hashes, actual selected word/context/span/box, request/run/PID/input correlation, overlay frame and return proofs. No requirement that the captured game itself supply narrative multiline context: existing oracle requires multiline/context diversity for Wesnoth, while captured routes require distinct actual source frames. [VERIFIED: tools/check_games.py:game_report changed_scenes predicate]

**Pilot budget / early stop:** Before code expansion, allow one launch/linkage setup and two resolutions (1280x800 then1024x768) at scale1 with default built-in font. At most one ordinary built-in alternative font/config is reasonable if default text is small; never replace assets. Stop this candidate if no genuine Wayland relative lock, no functioning software renderer, or neither actual heading produces valid production selection after those bounded attempts. Retain failures and return to A's saved-source regression path; do not start a third game catalogue or relax the oracle. A useful pilot still needs two complete accepted routes before closure. [Selected agent decisions under --auto]

## Narrow Integration Changes for Planning

[VERIFIED: tools/check_games.py/current aggregators] Current captured oracle hardcodes Freedoom name, Chocolate3.1.1 URLs/executable and scene `map01_captured_prompt`; current guest command accepts only wesnoth/doom. Extend with one explicit AssaultCube descriptor: fixed official URL/hash/size/version, owned executable/profile, validated scene `local_map_scoreboard`. Preserve exact same physical input, unchanged-source, span/box, useful frame, recent same-process lock and post-close controls assertions. Do not replace checks with a generic `source_verified:true` or arbitrary executable allowlist. Keep rejected Doom report/routes empty and referenced historically.

[VERIFIED: current tool source] Renderer observer currently relies on SDL_Renderer information suitable for Doom; AssaultCube creates SDL_GLContext instead. Use actual game's existing GL renderer/version log (and/or passive GL-context observation), hash it and bind it to actual game PID/start. Reuse existing SDL relative-mode/Wayland protocol observation, not a boolean inferred from a menu. Do not patch game rendering/input/source images.

[VERIFIED: check_hardening.py/check_hardening_install.py] Aggregate/cleanup currently expect Doom-specific report paths/keys. Teach them to consume a validated selected captured-game artifact and matching explicit cleanup record while preserving failed Doom history; never relabel Doom success. Cleanup must release keys, stop only owned game/observer/product processes, restore clone3D/shared-clipboard baseline, leave both VMs off and preserve Phase7 exception. New candidate has separate owned directory/process identity.

## Validation Architecture and Remaining Limits

[VERIFIED: verifier] Current host752 tests correspond to a10c5e1; previous target751/d5488b3 is stale. After final gap-closure implementation/evidence revisions, run fresh focused `tests.test_check_games`, relevant hardening/aggregation tests and any changed OCR regressions, then **full host and full target suite at the same recorded revision**. Record actual count/output/exit/source identity, do not promise a fixed new count. Independent review then verifier re-evaluates GAME-01 and aggregate raw gates.

Required durable negative tests: wrong candidate archive hash/URL/size/executable/UID, stale game PID/start, missing actual GL log, absent/unlocked/stale protocol, stage6/no Query, wrong word box, prior/false useful overlay, reused source/control frames or inputs and incomplete cleanup all reject acceptance. Existing Wesnoth/Doom rejection and actual timing/privacy behavior stay intact. If production OCR changes only after A evidence, add source-bound exact cursor/word regression plus existing noise/proximity/scales/multiline corpus; remeasure affected first-useful latency rather than assuming PERF-01 unchanged.

**Not verified by research:** native launch/llvmpipe, actual scoreboard text clarity, real lock while scoreboard open, successful selected Query/useful overlay and returned controls. Therefore GAME-01 remains blocked until those observed routes exist. No production fix, game run, VM operation, current target-suite refresh or acceptance waiver occurred here.

## Primary Sources

- https://assault.cubers.net/download.html — official release link/version, with stale dependency list explicitly distinguished.
- https://api.github.com/repos/assaultcube/AC/releases/tags/v1.3.0.2 — exact Linux asset URL and52071427byte size; digest absent.
- Official Linux archive above — SHA computed this session; included source/config/docs/ELF inspected in memory, no repository asset replacement.
- https://raw.githubusercontent.com/assaultcube/AC/v1.3.0.2/source/src/main.cpp — flags, focus/fullscreen and actual SDL2 grab calls.
- https://raw.githubusercontent.com/assaultcube/AC/v1.3.0.2/source/src/scoreboard.cpp — genuine headings and scoreboard control.
- https://raw.githubusercontent.com/assaultcube/AC/v1.3.0.2/source/src/rendergl.cpp — existing renderer/version output.
- https://raw.githubusercontent.com/assaultcube/AC/v1.3.0.2/config/font_default.cfg — shipped font provenance; no readability guarantee.
- https://docs.mesa3d.org/envvars.html — software-rendering request semantics.
- https://archlinux.org/packages/search/json/?name=assaultcube — zero official package results, independently fetched through urllib.
