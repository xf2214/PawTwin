import {chromium} from '../../../../../frontend/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const dir=path.dirname(fileURLToPath(import.meta.url));
const meta={createdAt:new Date().toISOString(),url:'http://127.0.0.1:8807/#cases',viewportCss:{width:1920,height:1080},deviceScaleFactor:2,physicalViewport:{width:3840,height:2160},kind:'High density stills; no video in this context.',shots:[],svgExports:[],requests:[],mutatingRequests:[],consoleErrors:[],pageErrors:[],httpErrors:[]};
const browser=await chromium.launch({channel:'chrome',headless:true});
const context=await browser.newContext({viewport:meta.viewportCss,deviceScaleFactor:2,locale:'en-US'});
const page=await context.newPage();
page.on('console',m=>{if(m.type()==='error')meta.consoleErrors.push(m.text());});page.on('pageerror',e=>meta.pageErrors.push(e.message));page.on('response',r=>{if(r.status()>=400)meta.httpErrors.push({status:r.status(),url:r.url()});});
await context.route('**/*',async route=>{const r=route.request();meta.requests.push({method:r.method(),url:r.url()});if(!['GET','HEAD','OPTIONS'].includes(r.method())){meta.mutatingRequests.push({method:r.method(),url:r.url()});await route.abort('blockedbyclient');}else await route.continue();});
async function capture(name,selector){const loc=page.locator(selector);await loc.waitFor({state:'visible'});const file=`${name}@2x.png`;await loc.screenshot({path:path.join(dir,file)});const bbox=await loc.boundingBox();meta.shots.push({name,file,selector,cssBox:bbox,pixelSize:{width:Math.round(bbox.width*2),height:Math.round(bbox.height*2)},text:await loc.innerText()});}
async function svg(name,selector){const loc=page.locator(selector).first();if(!await loc.count())return;const text=await loc.evaluate(el=>el.outerHTML);const file=`pet-${name}.actual-dom.svg`;await fs.writeFile(path.join(dir,file),text);meta.svgExports.push({name,file,selector,viewBox:await loc.getAttribute('viewBox'),source:'Unmodified outerHTML from the actual local showcase DOM.'});}
try{
 await page.goto(meta.url,{waitUntil:'networkidle'});await page.getByRole('button',{name:'Pause animations',exact:true}).click();await page.evaluate(()=>document.fonts.ready);
 await svg('mochi','.pt-hero-stage svg[viewBox="0 0 240 240"]');
 if(!meta.svgExports.some(s=>s.name==='mochi')){const all=await page.locator('.pt-hero-stage svg').evaluateAll(els=>els.map(el=>({viewBox:el.getAttribute('viewBox'),class:el.getAttribute('class'),length:el.outerHTML.length})));meta.mochiCandidateInfo=all;}
 await page.getByRole('button',{name:'Pet concierge',exact:true}).click();await page.locator('.pc-preview').waitFor();
 await capture('01-dog-full-panel','.pc-preview');await capture('01-dog-profile','.pc-profile');await capture('01-dog-question','.pc-owner-message');await capture('02-dog-reply','.pc-assistant-message');await capture('02-dog-boundary','.pc-demo-boundary');await svg('miso','.pc-pet-art svg');
 await page.getByRole('button',{name:/Cat wellbeing/}).click();await page.locator('.pc-activity').waitFor();
 await capture('03-cat-full-panel','.pc-preview');await capture('03-cat-profile','.pc-profile');await capture('03-cat-question','.pc-owner-message');await capture('03-cat-simulated-map','.pc-activity');await capture('04-cat-reply','.pc-assistant-message');await capture('04-cat-boundary','.pc-demo-boundary');await svg('luna','.pc-pet-art svg');
 await page.getByRole('button',{name:/Context included/}).click();await page.locator('.pc-comparison').waitFor();
 await capture('05-context-full-panel','.pc-preview');await capture('05-context-new-chat','.pc-new-session');await capture('05-context-included','.pc-pawtwin-session');await capture('05-context-boundary','.pc-demo-boundary');
 meta.verification={zeroBusinessPOST:meta.mutatingRequests.length===0,zeroBusinessRequests:meta.requests.filter(r=>new URL(r.url).pathname.startsWith('/api/')).length===0,zeroConsoleErrors:meta.consoleErrors.length===0,zeroPageErrors:meta.pageErrors.length===0,zeroHttpErrors:meta.httpErrors.length===0,englishOnly:!(await page.locator('.pc-preview').innerText()).match(/[\u4e00-\u9fff]/)};
 if(Object.values(meta.verification).some(v=>!v))throw new Error('High density capture verification failed');
}catch(e){meta.failure=e.message;process.exitCode=1;}finally{
 await browser.close();meta.files=[];for(const name of (await fs.readdir(dir)).filter(n=>/@2x\.png$|actual-dom\.svg$/.test(n))){const data=await fs.readFile(path.join(dir,name));meta.files.push({file:name,bytes:data.length,sha256:crypto.createHash('sha256').update(data).digest('hex')});}await fs.writeFile(path.join(dir,'capture-high-density-metadata.json'),JSON.stringify(meta,null,2));console.log(JSON.stringify(meta,null,2));
}
