"""Build the browser edition from the preserved OpenTyrian source and data."""
from pathlib import Path
import json
import difflib
import os
import shutil
import subprocess
import sys

lab = Path(__file__).resolve().parents[1]
source = lab
revision = "ac5d0e71f4245744350c6116ce24f10624da58f8"
sdk_value = os.environ.get("OPENTYRIAN_EMSDK") or os.environ.get("EMSDK")
if not sdk_value:
    raise SystemExit("Set OPENTYRIAN_EMSDK to your activated Emscripten 4.0.23 SDK directory.")
sdk = Path(sdk_value).resolve()
assert (sdk / "upstream/emscripten/emcc.py").is_file(), "Emscripten compiler not found"
name = sys.argv[1] if len(sys.argv) > 1 else "web"
assert name.replace("-", "").isalnum(), "Use an alphanumeric build directory name"
for entry in json.loads((lab / "browser/provenance/files.json").read_text(encoding="utf-8")):
    import hashlib
    actual = hashlib.sha256((lab / entry["path"]).read_bytes()).hexdigest()
    assert actual == entry["sha256"], "Source/data changed: " + entry["path"]
out = lab / "build" / name
out.mkdir(parents=True, exist_ok=True)
(out / "tmp").mkdir(exist_ok=True)
data = out / "data"
data.mkdir(exist_ok=True)
original = lab / "browser/data-original"
assert original.exists(), "Download the upstream-referenced data first"
for path in original.rglob("*"):
    if path.is_file():
        # Upstream explicitly requires lowercase names on case-sensitive systems.
        shutil.copy2(path, data / path.name.lower())
sources = sorted((source / "src").glob("*.c"))
if True:  # Browser-only generated override; native source is preserved.
    # Preserve the pinned checkout. Native builds still retain relative capture.
    original_input = (source / "src/keyboard.c").read_text(encoding="utf-8")
    needle = "\tSDL_SetRelativeMouseMode(enable && windowHasFocus);"
    assert original_input.count(needle) == 1
    browser_input = original_input.replace(needle, """#ifndef __EMSCRIPTEN__
	SDL_SetRelativeMouseMode(enable && windowHasFocus);
#endif
	// Browser canvas motion still supplies xrel/yrel below. Automatic native
	// pointer capture can reject outside a valid browser gesture/document.
	// Keep ordinary canvas mouse movement without trapping the browser cursor.""")
    modified = out / "overrides/keyboard.c"
    modified.parent.mkdir(exist_ok=True)
    modified.write_text(browser_input, encoding="utf-8")
    sources = [modified if p.name == "keyboard.c" else p for p in sources]
    (out / "browser-mouse.patch").write_text("".join(difflib.unified_diff(
        original_input.splitlines(True), browser_input.splitlines(True),
        fromfile="a/src/keyboard.c", tofile="b/src/keyboard.c"
    )), encoding="utf-8")
if True:  # Player bridge, pause and audio integration.
    keyboard = out / "overrides/keyboard.c"
    text = keyboard.read_text(encoding="utf-8")
    needle = "void handleSdlEvents(void)\n{"
    assert text.count(needle) == 1
    text = text.replace(needle, "extern void oga_poll(void);\n" + needle + "\n\toga_poll();")
    keyboard.write_text(text, encoding="utf-8")
    audio = (source / "src/loudness.c").read_text(encoding="utf-8")
    needle = "\n}\n\nvoid deinit_audio(void)"
    assert audio.count(needle) == 1
    audio = audio.replace(needle, "\n\textern void oga_audio_gate(Uint8 *, int);\n\toga_audio_gate(stream, size);" + needle)
    audio_file = out / "overrides/loudness.c"
    audio_file.write_text(audio, encoding="utf-8")
    sources = [audio_file if p.name == "loudness.c" else p for p in sources]
    sources.append(lab / "browser/web/browser.c")
    gameplay = (source / "src/tyrian2.c").read_text(encoding="utf-8")
    needle = "#ifdef NDEBUG\n\t\tif (pause_pressed || !windowHasFocus)"
    assert gameplay.count(needle) == 1
    gameplay = gameplay.replace(needle, "#if defined(NDEBUG) && !defined(__EMSCRIPTEN__)\n\t\tif (pause_pressed || !windowHasFocus)")
    # The page owns visibility pause. Focusing a touch-control button is not
    # leaving the game and must not trigger a second, invisible native pause.
    path = out / "overrides/tyrian2.c"
    path.write_text(gameplay, encoding="utf-8")
    sources = [path if p.name == "tyrian2.c" else p for p in sources]
cmd = [
    sys.executable, str(sdk / "upstream/emscripten/emcc.py"),
    *map(str, sources), "-std=c99", "-O2", "-DTARGET_UNIX", "-DNDEBUG",
    '-DTYRIAN_DIR="/data"', f'-DOPENTYRIAN_VERSION="web-{revision[:8]}"',
    "-sUSE_SDL=2", "-sASYNCIFY", "-sASYNCIFY_STACK_SIZE=65536",
    "-sSTACK_SIZE=1048576", "-sALLOW_MEMORY_GROWTH=1",
    "-sENVIRONMENT=web", "-sEXIT_RUNTIME=1", "-sASSERTIONS=1",
    "-sFORCE_FILESYSTEM=1", "--emit-symbol-map",
    "-I" + str(source / "src"),
    "-lidbfs.js",
    '-sEXPORTED_RUNTIME_METHODS=["FS","IDBFS","ENV","callMain","UTF8ToString","addRunDependency","removeRunDependency"]',
    "--preload-file", str(data) + "@/data", "-o", str(out / "tyrian.js"),
]
env = dict(os.environ, EM_CONFIG=str(sdk / ".emscripten"),
           EMSDK_PYTHON=sys.executable, EMCC_CORES="4",
           TEMP=str(out / "tmp"), TMP=str(out / "tmp"))
print(f"Building {revision}, {len(sources)} C compilation units", flush=True)
result = subprocess.run(cmd, env=env, cwd=source, timeout=240)
if result.returncode:
    raise SystemExit(result.returncode)
for filename in ["index.html", "input.js", "persistence.js", "bridge.js"]:
    shutil.copy2(lab / "browser/web" / filename, out / filename)
notice = "Tyrian: Eclipse Software / Epic MegaGames. OpenTyrian: The OpenTyrian Development Team.\nBrowser integration: Old Games Archive / CatBroDev.\nGame data is separately freeware, not GPL.\n"
for license_file in sorted((lab / "browser/licenses").iterdir()):
    notice += "\n=== " + license_file.name + " ===\n" + license_file.read_text(encoding="utf-8")
(out / "notices.txt").write_text(notice, encoding="utf-8")
shutil.copy2(lab / "COPYING", out / "COPYING")
shutil.copy2(lab / "README.md", out / "README.txt")
import zipfile
with zipfile.ZipFile(out / "source.zip", "w", zipfile.ZIP_DEFLATED) as archive:
    for directory in ["src", "browser"]:
        for item in sorted((lab / directory).rglob("*")):
            if item.is_file() and "__pycache__" not in item.parts:
                archive.write(item, item.relative_to(lab).as_posix())
    for filename in ["README.md", "README.upstream.md", "BUILD.md", "COPYING"]:
        archive.write(lab / filename, filename)
print("Browser build ready:", out, flush=True)
