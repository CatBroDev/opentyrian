# Build the browser edition

Requirements: Python 3 and an installed, activated **Emscripten 4.0.23 SDK**. This version uses **SDL2 2.32.8** from the SDK ports. The first compilation may download/cache the SDL2 port. There is no dependency on the private website repository. Node.js is optional for the storage regression test.

Clone this branch, preserving the upstream history:

```sh
git clone --branch codex/browser-restoration https://github.com/CatBroDev/opentyrian.git
cd opentyrian
```

Install and activate the SDK using the instructions in [emsdk](https://github.com/emscripten-core/emsdk). Point `OPENTYRIAN_EMSDK` at the SDK root containing `.emscripten` and `upstream/`, for example:

```sh
export OPENTYRIAN_EMSDK=/absolute/path/to/emsdk
python3 browser/build-web.py web
python3 -m http.server 8080 --directory build/web
```

On PowerShell use `$env:OPENTYRIAN_EMSDK = 'C:/path/to/emsdk'` and `python` in place of `python3`. Open `http://localhost:8080`, press **Start**, and use the keyboard. Sound starts muted. Stop the local server when finished. Opening `index.html` as a `file:` URL does not support this build.

The build checks `browser/provenance/files.json` before compilation. Intentional source changes require updating the corresponding hashes. It produces the runtime, license notices and a corresponding-source ZIP in `build/web`. Generated overrides live under that directory; `src/` is not rewritten.

## Storage regression

```sh
node browser/test-persistence.mjs
```

The test simulates a checkpoint still writing when native shutdown produces new settings. It verifies that both writes finish before IDBFS closes, that the final version is saved, and that a failed final write is reported without hanging. The browser acceptance also exercises this ordering against real IndexedDB, then restarts the browser and compares the native files.

## Embedding and source scope

`browser/web/bridge.js` implements the optional parent-frame protocol. It accepts messages only from the expected parent window and matching origin, then delegates keyboard input, pause, mute and shutdown to the compiled engine. A compatible host supplies the touch-control UI. The standalone page uses the keyboard and its own Start/Sound controls.

The included data is the upstream-distributed freeware Tyrian 2.1 release. Do not substitute Tyrian 2000 data or treat the game artwork/audio as GPL. See `browser/provenance/data-download.json` and the separate freeware notice.

Build options match the accepted browser release: C99, `-O2`, Asyncify, 64 KiB Asyncify stack, 1 MiB native stack, growable memory, IDBFS and SDL2. Diagnostic game-state exports are not part of this build. Network play is not enabled. See the README for remaining validation limits.
