/* Offline browser integration checks. All fabricated ratings stay under tmp/. */
const fs = require("fs");
const path = require("path");
const {pathToFileURL} = require("url");
const assert = require("assert/strict");
const {chromium} = require(process.env.AUDIT_PLAYWRIGHT_PATH ||
  "C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");

async function main() {
  const root = path.resolve(__dirname, "..");
  const output = path.join(root, "tmp/expert-audit-browser");
  fs.mkdirSync(output, {recursive:true});
  const folder = path.join(root, "experiments/t08-t09-expert-audit-v1");
  const packet = JSON.parse(fs.readFileSync(path.join(folder, "public/R01/packet.json"), "utf8"));
  const browser = await chromium.launch({
    executablePath: process.env.AUDIT_BROWSER || "C:/Program Files/Google/Chrome/Application/chrome.exe",
    headless:true,
  });
  const context = await browser.newContext({viewport:{width:1440,height:1050}, acceptDownloads:true});
  const requests = [], errors = [];
  await context.route(/^https?:/, route=>{requests.push(route.request().url());return route.abort()});
  const page = await context.newPage();
  page.on("pageerror", e=>errors.push(e.message));
  page.on("dialog", d=>d.accept());
  try {
    await page.goto(pathToFileURL(path.join(folder, "public/R01/index.html")).href);
    assert.equal(await page.locator("input[type=radio]:checked").count(), 0);
    assert.match(await page.locator("#progress").innerText(), /^0 \/ 120/);
    await page.locator("details.instructions > summary").click();
    await page.screenshot({path:path.join(output,"desktop.png"),fullPage:true});
    const first=page.locator("article").first();
    await first.locator("fieldset").first().getByRole("radio",{name:"3",exact:true}).check();
    await page.reload();
    assert.equal(await first.locator("fieldset").first().getByRole("radio",{name:"3",exact:true}).isChecked(),true);
    assert.equal(await first.locator("fieldset input[type=checkbox]").count(),0);
    await first.locator("fieldset").nth(1).getByRole("radio",{name:"2",exact:true}).check();
    assert.match(await page.locator("#progress").innerText(), /^1 \/ 120/);
    await page.locator("#final").click();
    assert.match(await page.locator("#notice").innerText(), /Unfinished/);
    const bad={...await page.evaluate(()=>window.Audit.getState()),rater_id:"R03"};
    await page.locator("#importFile").setInputFiles({name:"wrong-rater.json",mimeType:"application/json",buffer:Buffer.from(JSON.stringify(bad))});
    assert.match(await page.locator("#notice").innerText(), /Import rejected/);
    const synthetic={
      schema_version:2,packet_id:packet.packet_id,rater_id:packet.rater_id,
      rubric_version:packet.rubric_version,packet_version:packet.packet_version,position:0,ratings:{}
    };
    for(const pair of packet.pairs)for(const r of pair.responses)synthetic.ratings[r.answer_id]={
      relevance:{score:2},
      faithfulness:{score:3},
      note:"=SYNTHETIC TEST, not human evidence",flags:["No factual claims"],
      updated_at:"2026-10-20T00:00:00.000Z",
    };
    await page.locator("#importFile").setInputFiles({name:"synthetic.json",mimeType:"application/json",buffer:Buffer.from(JSON.stringify(synthetic))});
    assert.match(await page.locator("#progress").innerText(), /^120 \/ 120/);
    const badScoreResult = await page.evaluate(()=>{
      const s=JSON.parse(JSON.stringify(window.Audit.getState()));
      Object.values(s.ratings)[0].relevance.score=5;
      try{window.Audit.validate(s,true);return "accepted"}catch(e){return "rejected"}
    });
    assert.equal(badScoreResult,"rejected");
    const [jsonDownload]=await Promise.all([page.waitForEvent("download"),page.locator("#final").click()]);
    const jsonPath=path.join(output,"SYNTHETIC-R01-final.json");
    await jsonDownload.saveAs(jsonPath);
    const exported=JSON.parse(fs.readFileSync(jsonPath,"utf8"));
    assert.equal(exported.records.length,120);
    assert.equal(exported.export_kind,"final");
    assert.equal(exported.records[0].faithfulness_score,3);
    const [csvDownload]=await Promise.all([page.waitForEvent("download"),page.locator("#csv").click()]);
    const csvPath=path.join(output,"SYNTHETIC-R01-final.csv");
    await csvDownload.saveAs(csvPath);
    assert.match(fs.readFileSync(csvPath,"utf8"),/"'=SYNTHETIC TEST/);
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    // Restore a clean view for screenshots; use a new isolated context, not synthetic ratings.
    const clean=await browser.newContext({viewport:{width:390,height:844}});
    const mobile=await clean.newPage();
    await mobile.goto(pathToFileURL(path.join(folder,"public/R01/index.html")).href);
    await mobile.locator("details.instructions > summary").click();
    await mobile.screenshot({path:path.join(output,"mobile.png"),fullPage:true});
    await clean.close();
    assert.deepEqual(errors,[]);
    assert.deepEqual(requests,[]);
    const report={
      status:"PASS",checks:[
        "Blank initial scores", "Browser save/reload", "Only four ordinal score controls per dimension",
        "Incomplete export rejected", "Wrong-rater import rejected", "Draft import/resume",
        "Out-of-range score rejected", "120-row JSON export", "CSV formula escaping",
        "Mobile viewport overflow", "No JavaScript errors", "No network requests"
      ], synthetic_outputs:"tmp/expert-audit-browser only; not human ratings"
    };
    fs.writeFileSync(path.join(output,"browser_report.json"),JSON.stringify(report,null,2));
    console.log(JSON.stringify(report,null,2));
  } finally {
    await context.close();
    await browser.close();
  }
}
main().catch(e=>{console.error(e);process.exitCode=1});
