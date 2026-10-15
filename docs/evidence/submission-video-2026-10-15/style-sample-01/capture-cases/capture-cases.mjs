import { chromium } from '../../../../../frontend/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import crypto from 'node:crypto';
const dir=path.dirname(fileURLToPath(import.meta.url));
const meta={createdAt:new Date().toISOString(),url:'http://127.0.0.1:8807/#cases',viewport:{width:1920,height:1080},deviceScaleFactor:1,videoSize:{width:1920,height:1080},language:'en-US',dataBoundary:'Public fictional showcase only. Preset replies, simulated activity and web Alexa simulation. No app/business data, real AI, actual tracking or clinical diagnosis.',actions:[],shots:[],requests:[],mutatingRequests:[],consoleErrors:[],pageErrors:[],httpErrors:[],files:[]};
let browser,context,page,videoPath;
const started=Date.now();
function mark(action,detail={}){meta.actions.push({seconds:(Date.now()-started)/1000,action,...detail});}
async function settle(){await page.locator('.pc-preview').waitFor({state:'visible'});await page.evaluate(()=>document.fonts.ready);await page.waitForFunction(()=>document.querySelector('.showcase')?.getAttribute('data-motion')==='paused');}
async function boxes(){return await page.evaluate(()=>{const selectors={preview:'.pc-preview',topline:'.pc-topline',heading:'.pc-frame-heading',profile:'.pc-profile',contextRibbon:'.pc-context-ribbon',question:'.pc-owner-message',activity:'.pc-activity',reply:'.pc-assistant-message',answer:'.pc-answer',basis:'.pc-answer-basis',references:'.pc-references',detail:'.pc-frame-detail',boundary:'.pc-demo-boundary',comparison:'.pc-comparison',summary:'.pc-context-summary',newSession:'.pc-new-session',contextSession:'.pc-pawtwin-session',contextChips:'.pc-carried-context',caseLayout:'.pt-case-theme-3',steps:'#cases .pt-case-steps'};const result={scroll:{x:scrollX,y:scrollY},window:{width:innerWidth,height:innerHeight},dpr:devicePixelRatio,targets:{}};for(const [name,selector]of Object.entries(selectors)){const el=document.querySelector(selector);if(!el)continue;const r=el.getBoundingClientRect();result.targets[name]={selector,viewport:{x:r.x,y:r.y,width:r.width,height:r.height},document:{x:r.x+scrollX,y:r.y+scrollY,width:r.width,height:r.height},text:el.innerText??'',fontSize:getComputedStyle(el).fontSize};}return result;});}
async function shot(name,selector,top=110){const locator=page.locator(selector);await locator.waitFor({state:'visible'});await locator.evaluate((el,targetTop)=>window.scrollTo({top:el.getBoundingClientRect().top+scrollY-targetTop,behavior:'instant'}),top);await settle();const data=await boxes();const file=`${name}.1920x1080.png`;await page.screenshot({path:path.join(dir,file)});meta.shots.push({name,file,seconds:(Date.now()-started)/1000,...data});mark('capture_viewport',{name,file});}
async function crop(name,selector){const loc=page.locator(selector);const file=`${name}.crop.png`;await loc.screenshot({path:path.join(dir,file)});meta.shots.push({name,file,kind:'native_element_crop',seconds:(Date.now()-started)/1000,selector,...await boxes()});mark('capture_native_crop',{name,file,selector});}
try{
 browser=await chromium.launch({channel:'chrome',headless:true});
 context=await browser.newContext({viewport:meta.viewport,deviceScaleFactor:1,locale:'en-US',recordVideo:{dir,size:meta.videoSize}});
 page=await context.newPage();
 page.on('console',msg=>{if(msg.type()==='error')meta.consoleErrors.push(msg.text());});
 page.on('pageerror',e=>meta.pageErrors.push(e.message));
 page.on('response',r=>{if(r.status()>=400)meta.httpErrors.push({status:r.status(),url:r.url()});});
 await context.route('**/*',async route=>{const req=route.request();meta.requests.push({method:req.method(),url:req.url(),resourceType:req.resourceType()});if(!['GET','HEAD','OPTIONS'].includes(req.method())){meta.mutatingRequests.push({method:req.method(),url:req.url()});await route.abort('blockedbyclient');return;}await route.continue();});
 await page.goto(meta.url,{waitUntil:'networkidle'});mark('opened_public_showcase');
 await page.getByRole('button',{name:'Pause animations',exact:true}).click();mark('clicked_pause_animations');
 const concierge=page.getByRole('button',{name:'Pet concierge',exact:true});await concierge.click();mark('clicked_pet_concierge');await settle();
 await shot('01-dog-profile-question','.pc-topline',95);await page.waitForTimeout(1300);
 await crop('01-dog-full-panel','.pc-preview');await crop('01-dog-profile','.pc-profile');await crop('01-dog-question','.pc-owner-message');
 await shot('02-dog-reply','.pc-answer',320);await page.waitForTimeout(1700);await crop('02-dog-reply','.pc-assistant-message');await crop('02-dog-boundary','.pc-demo-boundary');
 await page.getByRole('button',{name:/Cat wellbeing/}).click();mark('clicked_cat_wellbeing');await settle();
 await shot('03-cat-profile-question-map','.pc-topline',95);await page.waitForTimeout(1700);await crop('03-cat-full-panel','.pc-preview');await crop('03-cat-profile','.pc-profile');await crop('03-cat-question','.pc-owner-message');await crop('03-cat-simulated-map','.pc-activity');
 await shot('04-cat-reply','.pc-answer',310);await page.waitForTimeout(1700);await crop('04-cat-reply','.pc-assistant-message');await crop('04-cat-boundary','.pc-demo-boundary');
 await page.getByRole('button',{name:/Context included/}).click();mark('clicked_context_included');await settle();
 await shot('05-context-comparison','.pc-topline',95);await page.waitForTimeout(1700);await crop('05-context-full-panel','.pc-preview');await crop('05-context-new-chat','.pc-new-session');await crop('05-context-included','.pc-pawtwin-session');await crop('05-context-boundary','.pc-demo-boundary');
 await shot('06-context-comparison-lower','.pc-comparison',120);await page.waitForTimeout(1700);
 meta.finalState={url:page.url(),buttons:await page.locator('#cases .pt-case-steps button').allTextContents(),pressed:await page.locator('#cases .pt-case-steps button[aria-pressed=true]').innerText(),english:!(await page.locator('.pc-preview').innerText()).match(/[\u4e00-\u9fff]/),...await boxes()};
 meta.verification={zeroBusinessPOST:meta.mutatingRequests.length===0,zeroBusinessRequests:meta.requests.filter(r=>new URL(r.url).pathname.startsWith('/api/')).length===0,zeroConsoleErrors:meta.consoleErrors.length===0,zeroPageErrors:meta.pageErrors.length===0,zeroHttpErrors:meta.httpErrors.length===0,nativeDprOne:meta.finalState.dpr===1};
 if(Object.values(meta.verification).some(v=>!v))throw new Error('Capture verification failed');
 mark('capture_complete');
 videoPath=await page.video().path();await context.close();context=null;meta.video={file:path.basename(videoPath),path:videoPath,kind:'native_browser_recording',containsRealClicks:true,encoding:'Playwright native WebM',size:meta.videoSize};
} catch(e){meta.failure=e.message;process.exitCode=1;} finally{
 if(context)await context.close();if(browser)await browser.close();
 const items=await fs.readdir(dir);for(const name of items.filter(n=>/\.(png|webm|mjs)$/.test(n))){const data=await fs.readFile(path.join(dir,name));meta.files.push({file:name,bytes:data.length,sha256:crypto.createHash('sha256').update(data).digest('hex')});}
 meta.elapsedSeconds=(Date.now()-started)/1000;await fs.writeFile(path.join(dir,'capture-metadata.json'),JSON.stringify(meta,null,2));console.log(JSON.stringify({verification:meta.verification,failure:meta.failure,elapsedSeconds:meta.elapsedSeconds,video:meta.video,shots:meta.shots.map(s=>({name:s.name,file:s.file,preview:s.targets.preview?.viewport,profile:s.targets.profile?.viewport,question:s.targets.question?.viewport,activity:s.targets.activity?.viewport,reply:s.targets.reply?.viewport,boundary:s.targets.boundary?.viewport})),files:meta.files},null,2));
}
