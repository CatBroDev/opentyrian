import vm from 'node:vm';
import fs from 'node:fs';
import assert from 'node:assert/strict';
const source=fs.readFileSync(new URL('./web/persistence.js',import.meta.url),'utf8');
const tick=()=>new Promise(r=>setImmediate(r));
for(const failedFinalWrite of [false,true]){
 const requests=[],events=[];let version=1,closed=false,mount;
 const Module={ENV:{},addRunDependency(){},removeRunDependency(){},
  IDBFS:{quit(){assert.equal(requests.length,0);closed=true;events.push('close');}},
  FS:{mkdirTree(){},mount(_fs,opts){mount=opts;},syncfs(populate,callback){
   assert(!closed,'Database closed while a save was starting');
   if(populate)return callback(null);
   requests.push({version,callback});events.push('write:'+version);
  }}};
 vm.runInNewContext(source,{Module});Module.preRun[0]();
 assert.equal(mount.autoPersist,false);
 const pending=Module.flushSaves();assert.equal(Module.flushSaves(),pending);
 version=2; // Native exit writes a newer configuration after the checkpoint.
 Module.IDBFS.quit();const shutdown=Module.shutdownSaves();
 assert(!closed);assert.equal(Module.flushSaves(),shutdown);
 const first=requests.shift();assert.equal(first.version,1);first.callback(null);
 await tick();assert(!closed);assert.equal(requests.length,1);
 const final=requests.shift();assert.equal(final.version,2);
 final.callback(failedFinalWrite?new Error('storage unavailable'):null);
 assert.equal(await shutdown,!failedFinalWrite);assert(closed);
 assert.equal(Module.storageState,failedFinalWrite?'unavailable':'available');
 assert.deepEqual(events,['write:1','write:2','close']);
 assert.equal(Module.shutdownSaves(),shutdown);
}
console.log('PASS: in-flight checkpoint drains, final native writes sync before close; failure is reported without hanging.');
