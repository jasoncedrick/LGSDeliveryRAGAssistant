// Synthetic browser checks. No benchmark records and no model calls.
const fs=require('fs'),path=require('path'),assert=require('assert');
const playwrightPath=process.env.AUDIT_PLAYWRIGHT_PATH||'C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright';
const {chromium}=require(playwrightPath);
const base=process.env.WEBSITE_TEST_URL||'http://127.0.0.1:8000';
const out=path.resolve('tmp/citizen-website');fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.AUDIT_BROWSER||'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 let disposition='ANSWERED',requests=0,lastPayload=null,queueStage='completed',temporaryPollFailure=false;
 let releaseHealth;const initialHealthGate=new Promise(resolve=>releaseHealth=resolve);
 await page.route('**/health',async route=>{await initialHealthGate;return route.fulfill({json:{status:'ready',message:'Ready to help'}});});
 await page.route('**/api/jobs',route=>{requests++;lastPayload=route.request().postDataJSON();return route.fulfill({status:202,json:{ticket:'synthetic-private-ticket'}});});
 await page.route('**/api/jobs/status',route=>{
   if(temporaryPollFailure){temporaryPollFailure=false;return route.abort();}
   if(queueStage==='expired')return route.fulfill({status:404,json:{detail:'This question has expired. Please submit it again.'}});
   if(queueStage!=='completed')return route.fulfill({json:{state:queueStage,ahead:2}});
   return route.fulfill({json:{state:'completed',result:{status:disposition,answer:disposition==='CLARIFICATION_REQUIRED'?'Which service do you mean?':'Synthetic browser test answer [S1]. <img src=x onerror="window.injected=true">',clarification_prompt:disposition==='CLARIFICATION_REQUIRED'?'Which service do you mean?':null,citation_labels_valid:true,citations:disposition==='CLARIFICATION_REQUIRED'?[]:[{citation:'S1',file_source:'BFP-CITIZENS-CHARTER-2022.pdf',pdf_relative_page:1,source_page:null,text:'SYNTHETIC TEST PASSAGE. Not service guidance.',source_url:'/sources/fire.pdf#page=1'}]}}});
 });
 await page.goto(base);assert(await page.locator('#send').isDisabled());releaseHealth();await page.locator('#send:not([disabled])').waitFor();
 await page.screenshot({path:path.join(out,'desktop.png'),fullPage:true});
 assert.equal(await page.locator('.suggestion').count(),3);
 await page.getByRole('button',{name:'Planning',exact:true}).click();
 await page.locator('.suggestion').first().click();assert((await page.locator('#question').inputValue()).includes('locational'));
 const originalQuestion=await page.locator('#question').inputValue();
 await page.locator('#response-language').selectOption('bislish');
 await page.locator('#send').click();await page.locator('.copy-answer').waitFor();assert.equal(requests,1);
 assert.deepEqual(lastPayload,{query:originalQuestion,response_language:'bislish'});
 await page.locator('#response-language').selectOption('auto');
 assert.equal(await page.locator('.message-body img').count(),0);assert.equal(await page.evaluate(()=>window.injected),undefined);
 await page.locator('.citation-link').click();assert(await page.locator('.evidence').evaluate(e=>e.open));
 assert.equal(await page.locator('.source-card a').getAttribute('href'),'/sources/fire.pdf#page=1');
 await page.screenshot({path:path.join(out,'answer-synthetic.png'),fullPage:true});
 await page.locator('#new-question').click();assert.equal(await page.locator('.message').count(),0);
 disposition='CLARIFICATION_REQUIRED';await page.locator('#question').fill('Synthetic ambiguous inquiry');await page.locator('#send').click();await page.locator('.notice').waitFor();assert((await page.locator('.notice').innerText()).includes('full question'));
 await page.locator('#new-question').click();disposition='GENERATION_INCOMPLETE';await page.locator('#question').fill('Synthetic incomplete inquiry');await page.locator('#send').click();await page.locator('.notice').waitFor();assert((await page.locator('.notice').innerText()).includes('cut short'));
 await page.locator('#new-question').click();
 await page.getByRole('link',{name:'Source library',exact:false}).click();await page.locator('.library-card').first().waitFor();assert.equal(await page.locator('.library-card').count(),5);
 await page.reload();await page.locator('.library-card').first().waitFor(); // Direct hash navigation must work.
 await page.getByRole('link',{name:'About this project',exact:false}).click();await page.locator('#about-title').waitFor();assert(await page.locator('#about-title').isVisible());
 await page.setViewportSize({width:390,height:844});await page.locator('#new-question').click();
 await page.screenshot({path:path.join(out,'mobile.png'),fullPage:true});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.unroute('**/health');await page.route('**/health',route=>route.fulfill({json:{status:'model_offline',message:'The answer service is offline.'}}));
 await page.locator('#check-connection').click();await page.waitForFunction(()=>document.querySelector('#send').disabled);assert(await page.locator('#connection-note').isVisible());
 await page.unroute('**/health');await page.route('**/health',route=>route.fulfill({json:{status:'ready',message:'Ready'}}));await page.locator('#check-connection').click();await page.locator('#send:not([disabled])').waitFor();
 queueStage='queued';disposition='ANSWERED';await page.locator('#question').fill('Synthetic waiting visitor');
 const beforeQueue=requests;await page.locator('#send').click();await page.getByText('2 questions ahead of yours.',{exact:false}).waitFor();assert(await page.locator('#send').isDisabled());
 await page.screenshot({path:path.join(out,'queue-synthetic.png'),fullPage:true});
 queueStage='running';await page.getByText('Preparing your answer from the charter sources.',{exact:false}).waitFor();
 temporaryPollFailure=true;await page.getByText('Reconnecting to your question.',{exact:false}).waitFor();
 queueStage='completed';await page.locator('.copy-answer').waitFor();assert.equal(requests,beforeQueue+1);
 await page.locator('#new-question').click();queueStage='expired';await page.locator('#question').fill('Synthetic expired question');await page.locator('#send').click();await page.locator('.message.error').waitFor();assert.equal(await page.locator('#question').inputValue(),'Synthetic expired question');
 await page.locator('#new-question').click();queueStage='completed';
 await page.unroute('**/api/jobs');await page.route('**/api/jobs',route=>route.fulfill({status:429,json:{detail:'The assistant is helping someone else.'}}));
 await page.locator('#question').fill('Synthetic capacity check');await page.locator('#send').click();await page.locator('.message.error').waitFor();assert.equal(await page.locator('#question').inputValue(),'Synthetic capacity check');
 assert.deepEqual(errors,[]);await browser.close();
 const report={passed:true,synthetic:true,model_calls:0,checks:['submit waits for initial readiness','desktop layout','topic suggestions','submit contract','language selector preserves original question','citation link and source passage','XSS text safety','new question reset','clarification handling','incomplete answer handling','five-source library','direct hash navigation','about page','mobile overflow','offline recovery','queue position and running progress','poll reconnection without duplicate submission','expired ticket preserves question','capacity error preserves question'],browser_errors:errors};
 fs.writeFileSync(path.join(out,'browser-qa.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
})().catch(e=>{console.error(e);process.exit(1)});
