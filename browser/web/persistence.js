/* Native save slots/settings, GPL-2.0-or-later, Old Games Archive / CatBroDev. */
(() => {
  Module.storageState='loading';
  const status=state=>{Module.storageState=state;Module.onStorageState?.(state);};
  let pending, shutdown;
  const flush=()=>pending??=(new Promise(resolve=>{
    try { Module.FS.syncfs(false,error=>{status(error?'unavailable':'available');resolve(!error);}); }
    catch(error) { status('unavailable');resolve(false); }
  }).finally(()=>{pending=null;}));
  Module.flushSaves=()=>shutdown??flush();
  Module.preRun=[()=>{
    const {FS,IDBFS}=Module;
    Module.ENV.XDG_CONFIG_HOME='/persistent';
    FS.mkdirTree('/persistent');
    // A single explicit writer owns persistence. Auto-persist would create a
    // second queue racing the final save and Emscripten's synchronous quit.
    FS.mount(IDBFS,{autoPersist:false},'/persistent');
    const close=IDBFS.quit.bind(IDBFS);
    Module.shutdownSaves=()=>shutdown??=(async()=>{
      await pending; // Let any previous snapshot finish before the last write.
      const saved=await flush(); // Includes native JE_tyrianHalt's final writes.
      close();
      return saved;
    })();
    // Runtime exit cannot await IDBFS. Defer only its connection close; native
    // shutdown/FS stream cleanup and Module.onExit still run normally.
    IDBFS.quit=()=>{Module.shutdownSaves();};
    Module.addRunDependency('opentyrian-saves');
    FS.syncfs(true,error=>{status(error?'unavailable':'available');Module.removeRunDependency('opentyrian-saves');});
  }];
})();
