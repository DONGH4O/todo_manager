import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
// Connect only to a shell launched with an isolated empty/synthetic --data-dir.
// This smoke writes one task and one subtask; it is not a test against user data.
if (!process.argv.includes('--isolated-test-data')) throw Error('Pass --isolated-test-data after launching a dedicated test instance');
const port=Number(process.argv[2]||9235);
const targets=await(await fetch(`http://127.0.0.1:${port}/json`)).json();
const target=targets.find(t=>t.type==='page');
if(!target)throw Error('No QtWebEngine page');
const socket=new WebSocket(target.webSocketDebuggerUrl);
await new Promise((ok,bad)=>{socket.onopen=ok;socket.onerror=bad;});
let id=0;const pending=new Map();
socket.onmessage=e=>{const r=JSON.parse(e.data);if(r.id){const p=pending.get(r.id);pending.delete(r.id);r.error?p.reject(Error(JSON.stringify(r.error))):p.resolve(r.result);}};
const call=(method,params={})=>new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});socket.send(JSON.stringify({id:n,method,params}));});
const evaluate=async(expression)=>{const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const click=async(selector)=>{const pt=await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw Error('Missing '+${JSON.stringify(selector)});const r=e.getBoundingClientRect();const hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);if(!e.contains(hit)&&hit!==e)throw Error('Covered control '+${JSON.stringify(selector)});return{x:r.x+r.width/2,y:r.y+r.height/2};})()`);await call('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...pt});await call('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,...pt});await sleep(30);};
const check=async()=>evaluate(`(()=>{const o=document.querySelector('[role="dialog"]'),p=o?.querySelector('.tm-modal-panel'),input=p?.querySelector('input');if(!o||!p||!input)throw Error('Modal not rendered');const so=getComputedStyle(o),sp=getComputedStyle(p),rect=input.getBoundingClientRect(),hit=document.elementFromPoint(rect.x+rect.width/2,rect.y+rect.height/2);if(so.backdropFilter!=='none'||sp.opacity!=='1'||sp.visibility!=='visible'||sp.display==='none'||hit!==input||o.parentElement!==document.body)throw Error('Modal rendering invariant failed');if(document.documentElement.dataset.desktopShell!=='true')throw Error('Missing desktop policy');return{backdropFilter:so.backdropFilter,panelBackground:sp.backgroundColor,transition:sp.transitionDuration,portal:true,viewport:[innerWidth,innerHeight],devicePixelRatio};})()`);
await call('Page.reload');await sleep(600);
const before=await evaluate(`window.todoBridge.request({action:'listTasks'})`);
if(!before.ok||before.result.some(t=>!t.title.startsWith('测试样例')))throw Error('Smoke requires isolated synthetic test data');
const baselineCount=before.result.length;
const evidence=[];
for(const scale of [{width:2560,height:1440,deviceScaleFactor:1.5},{width:1920,height:1080,deviceScaleFactor:2}]){
 await call('Emulation.setDeviceMetricsOverride',{...scale,mobile:false});
 for(const theme of ['明色','暗色']){
  await evaluate(`(()=>{const b=[...document.querySelectorAll('button')].find(b=>b.textContent.includes(${JSON.stringify(theme)}));if(!b)throw Error('Theme unavailable');b.click();})()`);
  for(let round=0;round<5;round++){
   await click('button[aria-label="新建任务"]');await sleep(50);evidence.push(await check());
   await click('[role="dialog"] input');
   for(const word of ['4K','弹窗','连续输入','测试']){await call('Input.insertText',{text:word});await check();}
   await click('[role="dialog"] textarea');await call('Input.insertText',{text:'验证标题输入与备注输入后弹窗仍可绘制。'.repeat(8)});await check();
   await click('[role="dialog"] button[aria-label="选择开始日期"]');
   if(!await evaluate(`!!document.querySelector('.tm-date-popover')`))throw Error('Date picker missing');
   await click('[role="dialog"] button[aria-label="选择开始日期"]');
   await click('[role="dialog"] button[aria-label="选择任务状态"]');
   await click('[role="listbox"] [role="option"]:nth-child(2)');
   await check();
   if(round===4&&scale.deviceScaleFactor===1.5&&theme==='明色'){
    await click('[role="dialog"] button[aria-label="创建任务"]');await sleep(300);
    const r=await evaluate(`window.todoBridge.request({action:'listTasks'})`);
    if(!r.ok||r.result.length!==baselineCount+1||r.result.find(t=>t.title==='4K弹窗连续输入测试')?.status!=='完成中')throw Error('Created task did not roundtrip');
    // Keep later rounds isolated too; the backend list must remain readable.
   }else await click('[role="dialog"] button[aria-label="取消"]');
  }
 }
}
await click('button[aria-label="新建任务"]');await check();
if(await evaluate(`document.querySelector('[role="dialog"] input').value`)!='')throw Error('Stale draft on reopening');
const image=await call('Page.captureScreenshot',{format:'png'});
fs.writeFileSync(path.join(os.tmpdir(), 'todomanager-flicker-modal.png'),Buffer.from(image.data,'base64'));
await click('[role="dialog"] button[aria-label="取消"]');
// Verify subtask input survived the performance-branch ref optimization.
await click('button[aria-label="新增子任务"]');
await click('[role="dialog"] input');await call('Input.insertText',{text:'子任务输入验证'});
await click('[role="dialog"] button[aria-label="添加子任务"]');await sleep(250);
const after=await evaluate(`window.todoBridge.request({action:'listTasks'})`);
if(!after.ok||after.result.find(t=>t.title==='4K弹窗连续输入测试')?.subtasks[0]?.title!=='子任务输入验证')throw Error('Subtask save failed');
fs.writeFileSync(path.join(os.tmpdir(), 'todomanager-flicker-ui-results.json'),JSON.stringify({port,modalRounds:evidence.length,sourceURL:target.url,evidence,taskSaved:true,subtaskSaved:true},null,2));
console.log(JSON.stringify({modalRounds:evidence.length,scales:[1.5,2],lightAndDark:true,taskSaved:true,subtaskSaved:true,cssAndHitTesting:true}));
socket.close();
