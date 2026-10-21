/* Browser lifecycle integration, Old Games Archive / CatBroDev, 2026.
 * GPL-2.0-or-later. Original engine and gameplay remain OpenTyrian's. */
#include <emscripten.h>
#include <stdbool.h>
#include <string.h>
#include "SDL.h"
#include "keyboard.h"
#include "config.h"
#include "varz.h"

static bool paused = false, stopping = false, muted = true, ready = false;
EM_JS(void, oga_notify_ready, (void), { Module.onGameReady && Module.onGameReady(); });

EMSCRIPTEN_KEEPALIVE void oga_release(void)
{
    memset(keysactive, 0, sizeof keysactive);
    memset(lordKeySymsDown, 0, sizeof lordKeySymsDown);
    mouseButtonsDown = 0;
    keyboardClearInput();
    mouseClearInput();
    SDL_FlushEvents(SDL_KEYDOWN, SDL_MOUSEWHEEL);
}

EMSCRIPTEN_KEEPALIVE void oga_pause(int value)
{
    oga_release();
    paused = value != 0;
}
EMSCRIPTEN_KEEPALIVE int oga_paused(void) { return paused; }
EMSCRIPTEN_KEEPALIVE void oga_mute(int value) { muted = value != 0; }
EMSCRIPTEN_KEEPALIVE void oga_stop(void) { stopping = true; paused = false; }
EMSCRIPTEN_KEEPALIVE void oga_checkpoint(void)
{
    if (!ready) return;
    saveConfiguration();
    saveSaves();
}
void oga_audio_gate(Uint8 *stream, int length)
{
    if (muted || paused || stopping) memset(stream, 0, length);
}
void oga_poll(void)
{
    if (!ready) {
        ready = true;
        oga_notify_ready();
    }
    while (paused && !stopping) emscripten_sleep(16);
    if (stopping) JE_tyrianHalt(0);
}
