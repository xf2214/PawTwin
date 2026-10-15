const path=require('node:path');
const fs=require('node:fs');
const {bundle}=require('@remotion/bundler');
const {openBrowser,selectComposition,renderStill}=require('@remotion/renderer');
(async()=>{
 const output=path.join(__dirname,'qa','fullfilm-01');fs.mkdirSync(output,{recursive:true});
 const serveUrl=await bundle({entryPoint:path.join(__dirname,'src/index.tsx')});
 const browser=await openBrowser('chrome',{browserExecutable:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 try{
  const composition=await selectComposition({serveUrl,id:'PawTwinHackathonFilm',puppeteerInstance:browser});
  for(const frame of [54,334,507,655,828,1069,1300,1430,1510,1605,1840,1950,2140,2290,2440,2570,2720,2910,3070,3280,3510,3760,3940,4180]){
   await renderStill({serveUrl,composition,frame,output:path.join(output,`planned-${String(frame).padStart(4,'0')}.png`),imageFormat:'png',puppeteerInstance:browser});
  }
  console.log('24 complete-film preflight frames rendered');
 }finally{await browser.close({silent:true});}
})().catch(e=>{console.error(e);process.exitCode=1;});
