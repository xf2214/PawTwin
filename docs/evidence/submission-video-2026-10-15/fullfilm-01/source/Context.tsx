import React from 'react';
import {Brand,Canvas,CaptionLine,C,Footnote,Kicker,Pet,Reveal,VideoCrop} from './design';

export const Context = () => <Canvas dark><Brand light note="THE CONTEXT COMES ALONG"/>
  <Reveal style={{position:'absolute',left:112,top:153,width:650}}><Kicker>02 / A FRESH CONVERSATION</Kicker><div style={{fontFamily:'PawDisplay',fontSize:86,lineHeight:1.09,marginTop:30}}>A fresh chat.<br/><span style={{color:'#C9D7B8'}}>Same Mochi.</span></div></Reveal>
  <div style={{position:'absolute',left:112,top:453,fontSize:30,lineHeight:1.4,color:'#C9D7B8'}}>Confirmed preference,<br/>with its record source.</div>
  <div style={{position:'absolute',left:112,top:620,padding:'15px 25px',border:'1px solid #6B8972',borderRadius:30,fontSize:26}}>Alex · Carer</div>
  <Reveal delay={.2} style={{position:'absolute',left:380,top:600}}><Pet name="mochi" size={190}/></Reveal>
  <Reveal delay={.1}><VideoCrop src="alexa-crop.mp4" crop={[0,0,800,650]} sourceSize={[800,650]} x={850} y={165} width={958} hold={{after:5.8,src:'alexa-hold.png'}}/></Reveal>
  <CaptionLine light captions={[{text:'Alex starts fresh. The same context comes along.',startMs:501,endMs:5000,timestampMs:null,confidence:null}]}/>
  <Footnote light>ALEXA WEB SIMULATION · LOCAL RULES · ACTUAL UI</Footnote>
</Canvas>;
