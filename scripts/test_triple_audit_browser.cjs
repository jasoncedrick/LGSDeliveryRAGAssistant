const {chromium}=require('C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {pathToFileURL}=require('url');
const path=require('path'),fs=require('fs');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 const results=[];
 for(const mod of ['M1','M2']){
  const page=await browser.newPage({viewport:{width:1500,height:1000}});let errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(pathToFileURL(path.resolve('experiments/t08-t09-expert-audit-v2-triple/public/R01-'+mod+'/index.html')).href);
  const result=await page.evaluate(()=>{
   const a=window.Audit;const expected=a.packet.module==='M1'?80:180;
   if(document.querySelectorAll('#responses article').length!==(expected===80?2:3))throw Error('cards');
   if(!document.getElementById('progress').textContent.includes(String(expected)))throw Error('progress');
   const state=a.getState();const dims=expected===80?['fidelity']:['relevance','faithfulness'];
   try{a.validate(state,true);throw Error('accepted incomplete')}catch(e){if(e.message==='accepted incomplete')throw e;}
   for(const p of a.packet.pairs)for(const r of p.responses){state.ratings[r.answer_id]={note:'SYNTHETIC ONLY',flags:[],updated_at:new Date().toISOString()};for(const d of dims)state.ratings[r.answer_id][d]={score:expected===80?5:4};}
   a.validate(state,true);if(a.exportRows().length!==expected)throw Error('rows');
   const wrong={...state,packet_version:'old'};try{a.validate(wrong);throw Error('accepted old')}catch(e){if(e.message==='accepted old')throw e;}
   return {module:a.packet.module,rows:a.exportRows().length,identity:document.getElementById('identity').textContent};
  });
  await page.setViewportSize({width:390,height:844});
  if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1))throw Error('mobile overflow');
  if(errors.length)throw Error(errors.join(';'));
  results.push(result);await page.close();
 }
 await browser.close();console.log(JSON.stringify(results,null,2));
})().catch(e=>{console.error(e);process.exit(1)});
