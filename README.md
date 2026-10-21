# OpenTyrian — Old Games Archive browser build

Play the original Tyrian 2.1 campaign in a browser, using the community OpenTyrian C port. This unofficial integration adds browser storage, pause, audio and input lifecycle fixes; it does not replace the original game engine.

- [Play OpenTyrian](https://oldgamesarchive.org/games/opentyrian)
- [中文介绍与试玩](https://oldgamesarchive.org/zh-cn/games/opentyrian)
- [Build this version](BUILD.md)
- [Original OpenTyrian README](README.upstream.md)
- [Upstream project](https://github.com/opentyrian/opentyrian)

## Authors and licenses

Tyrian was created by **Eclipse Software / Epic MegaGames (1995)**. The C port is by **The OpenTyrian Development Team and contributors**. Their original history, source headers and copyright notices are retained. Browser integration and maintenance: Old Games Archive / **CatBroDev**.

OpenTyrian and this browser integration are GPL-2.0-or-later. The DOSBox OPL implementation retains its LGPL-2.1-or-later notice and Ken Silverman's ADLIBEMU attribution. The included **Tyrian 2.1 game data is separately freeware, not GPL**; see [its original notice](browser/licenses/Tyrian-freeware.txt) and [the dependency licenses](browser/licenses).

This edition has four episodes, not Tyrian 2000's fifth episode. Source baseline: `ac5d0e71f4245744350c6116ce24f10624da58f8`. Data comes from the upstream `v2.1.20260913` Linux release; [provenance and checksums](browser/provenance) are included.

## Browser changes

- Compile the original C engine through Emscripten/SDL2 and Asyncify.
- Restore native settings and save slots from IndexedDB before starting.
- Serialize storage writes; drain an in-flight checkpoint, write the final native configuration, and only then close IndexedDB at exit. Failed storage writes are reported instead of claiming the save succeeded.
- Release held keys when interrupted, and support simultaneous keys from the site's shared configurable touch controller.
- Let the host own visibility pause. Touching a button must not trigger a second invisible pause through native window-focus handling.
- Gate the actual audio output on mute/pause and close audio on shutdown.
- Keep ordinary canvas mouse input without automatic pointer capture.

Native source files remain unchanged: the builder generates browser-only overrides in `build/`. The standalone build also works without the website.

## Controls and saves

| Key | Action |
| --- | --- |
| Arrow keys | Move; navigate menus |
| Space | Fire |
| Enter | Change rear firing mode; confirm menus |
| Left Ctrl / Left Alt | Left / right sidekick, when equipped |
| P | Pause; a non-modifier key resumes |
| Esc | Open the game menu or go back |

In Full Game mode, choose **Play Next Level** in the equipment shop. Native save slots resume at a level boundary, not at an arbitrary instant during combat. Saves are local to this browser and origin; clearing browser data removes them. This is not cloud saving or DOS snapshot import.

## Validation and limits

The published build was tested for startup, movement, firing, native save/load, browser restart, visibility pause, mute, shutdown, and delayed storage writes during exit. The publication build is rebuilt separately from this repository. `node browser/test-persistence.mjs` covers both successful and failed final writes. Desktop touch emulation is not physical Android/iOS validation, and the four-episode campaign has not been played through in full.

Single-player browser play is the tested scope. Network play is not compiled in. The original game screens remain English; the website provides English and Chinese instructions.

Upstream already has a separate [WebAssembly proposal, PR #79](https://github.com/opentyrian/opentyrian/pull/79). This branch is an independently maintained integration based on the pinned upstream source. It does not claim to be the first web port or to have recovered the lost original Pascal source.
