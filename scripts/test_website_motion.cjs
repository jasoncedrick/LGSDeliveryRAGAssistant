// Presentation-only regression checks. All model endpoints are mocked.
const {chromium}=require(process.env.AUDIT_PLAYWRIGHT_PATH||'C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('assert'),fs=require('fs');
const base=process.env.WEBSITE_TEST_URL||'http://127.0.0.1:8000';
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.AUDIT_BROWSER||'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 const checks=[],errors=[];
 const context=await browser.newContext({viewport:{width:1440,height:1000}});
 const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 await context.route('**/health',r=>r.fulfill({json:{status:'ready',message:'Ready'}}));
 await context.route('**/api/query',r=>r.fulfill({json:{status:'ANSWERED',answer:'Synthetic response [S1].',citations:[],citation_labels_valid:true}}));
 await page.goto(base);await page.locator('#send:not([disabled])').waitFor();
 assert(await page.evaluate(()=>!!window.gsap&&!!window.Lenis));checks.push('local GSAP and Lenis loaded');
 await page.waitForTimeout(650);
 assert.equal(await page.locator('#welcome-title').evaluate(n=>getComputedStyle(n).opacity),'1');
 assert.equal(await page.locator('#question').evaluate(n=>parseFloat(getComputedStyle(n).fontSize)),17);
 checks.push('entrance settles; readable input');
 await page.screenshot({path:'tmp/website-motion/desktop.png',fullPage:true});
 await page.getByRole('link',{name:'About this project',exact:false}).click();
 await page.waitForFunction(()=>document.documentElement.dataset.smoothScroll==='on');
 assert(await page.evaluate(()=>document.documentElement.classList.contains('lenis')));checks.push('Lenis active on desktop information page');
 await page.mouse.wheel(0,500);await page.waitForTimeout(800);assert(await page.evaluate(()=>scrollY>0));checks.push('wheel scroll advances');
 await page.locator('#motion-toggle').click();assert.equal(await page.locator('#motion-toggle').getAttribute('aria-pressed'),'false');
 assert(await page.evaluate(()=>!document.documentElement.classList.contains('lenis')));
 await page.reload();assert.equal(await page.locator('#motion-toggle').getAttribute('aria-pressed'),'false');checks.push('motion opt-out persists and destroys Lenis');
 await page.locator('#motion-toggle').click();
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.waitForFunction(()=>document.documentElement.dataset.motion==='off');
 assert(await page.locator('#motion-toggle').isDisabled());assert(await page.evaluate(()=>!document.documentElement.classList.contains('lenis')));checks.push('OS reduced motion overrides all effects');
 await page.emulateMedia({reducedMotion:'no-preference'});
 await page.locator('#new-question').click();await page.waitForFunction(()=>document.documentElement.dataset.smoothScroll==='off');checks.push('chat retains native scroll');
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:'tmp/website-motion/mobile.png',fullPage:true});
 let composer=await page.locator('#question-form').boundingBox(),suggestions=await page.locator('#suggestions').boundingBox();assert(composer.y<suggestions.y);checks.push('mobile question form precedes suggestions');
 for(const width of [320,390,768]){
  await page.setViewportSize({width,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 }
 checks.push('no horizontal overflow at 320/390/768');
 await page.setViewportSize({width:390,height:844});
 await page.locator('#question').focus();await page.keyboard.type('Synthetic keyboard check');await page.keyboard.press('Enter');await page.locator('.copy-answer').waitFor();checks.push('keyboard submission works');
 await context.close();
 const fallback=await browser.newContext();const bare=await fallback.newPage();bare.on('pageerror',e=>errors.push(e.message));
 await bare.route('**/assets/vendor/**',r=>r.abort());
 await bare.route('**/health',r=>r.fulfill({json:{status:'ready'}}));
 await bare.goto(base);await bare.locator('#send:not([disabled])').waitFor();assert(await bare.locator('#welcome-title').isVisible());await bare.locator('#question').fill('No animation dependencies');checks.push('content/form remain usable if vendor scripts fail');
 assert.deepEqual(errors,[]);await browser.close();
 const report={passed:true,model_calls:0,checks,browser_errors:errors};fs.writeFileSync('tmp/website-motion/qa.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
})().catch(e=>{console.error(e);process.exit(1)});
