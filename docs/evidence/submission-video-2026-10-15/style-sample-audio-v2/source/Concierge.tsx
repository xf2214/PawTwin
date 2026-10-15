import React from 'react';
import {Easing,interpolate,Sequence,useCurrentFrame,useVideoConfig} from 'remotion';
import {Brand,Canvas,CaptionLine,C,Footnote,Kicker,Picture,Reveal} from './design';

const Miso = () => {
  const frame=useCurrentFrame(); const {fps}=useVideoConfig();
  const p=interpolate(frame,[1.65*fps,2.25*fps],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.bezier(.16,1,.3,1)});
  return <>
    <Reveal style={{position:'absolute',left:112,top:161,width:660}}><Kicker>PRODUCT PREVIEW / MISO</Kicker><div style={{fontFamily:'PawDisplay',fontSize:85,lineHeight:1.08,letterSpacing:-1.5,marginTop:22}}>Know Miso.<br/><span style={{color:C.sage}}>Then respond.</span></div></Reveal>
    <div style={{position:'absolute',left:816-704*p,top:174+326*p}}><Picture src="01-dog-profile@2x.png" width={992-337*p} style={{borderRadius:24,boxShadow:'0 24px 65px #254B3310'}}/></div>
    <Reveal delay={.55} style={{position:'absolute',right:112,top:600-430*p}}><Picture src="01-dog-question@2x.png" width={625-60*p} style={{borderRadius:20}}/></Reveal>
    <Reveal delay={2.05} style={{position:'absolute',left:850,top:384}}><Picture src="02-dog-reply@2x.png" width={958} style={{borderRadius:24,boxShadow:'0 24px 65px #254B3310'}}/></Reveal>
    <div style={{position:'absolute',left:112,top:803,fontSize:28,color:C.sage,opacity:p}}>Profile + confirmed preference → reply</div>
  </>;
};

const Luna = () => {
  const frame=useCurrentFrame(); const {fps}=useVideoConfig();
  const focus=Math.min(2,Math.max(0,Math.floor((frame/fps-.45)/1.1)));
  return <>
  <Reveal style={{position:'absolute',left:112,top:158,width:650}}><Kicker>PRODUCT PREVIEW / LUNA</Kicker><div style={{fontFamily:'PawDisplay',fontSize:88,lineHeight:1.05,letterSpacing:-1.5,marginTop:22}}>Start with<br/><span style={{color:C.sage}}>what you know.</span></div></Reveal>
  <Reveal delay={.15} style={{position:'absolute',left:112,top:497}}><Picture src="03-cat-profile@2x.png" width={655} style={{borderRadius:24}}/></Reveal>
  <Reveal delay={.05} style={{position:'absolute',left:850,top:312}}><Picture src="03-cat-simulated-map@2x.png" width={958} style={{borderRadius:28,boxShadow:'0 24px 65px #254B3310'}}/></Reveal>
  <Reveal delay={.35} style={{position:'absolute',left:850,top:219,fontSize:29,color:C.sage}}>Illustrative activity records</Reveal>
  <div style={{position:'absolute',left:936+focus*302,top:665,width:183,height:78,border:'3px solid #7E9B6F',borderRadius:14,opacity:interpolate(frame,[.4*fps,.7*fps],[0,.75],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})}}/>
</>;
};

export const Concierge:React.FC<{misoSeconds?:number;totalSeconds?:number}> = ({misoSeconds=6.3,totalSeconds=10.7}) => {
  const {fps}=useVideoConfig(); const f=useCurrentFrame();
  return <Canvas><Brand note="SCRIPTED PET CONCIERGE PREVIEW"/>
    <Sequence name="Miso's food question" from={0} durationInFrames={Math.round(misoSeconds*fps)} premountFor={fps}><Miso/></Sequence>
    <Sequence name="Luna's activity records" from={Math.round(misoSeconds*fps)} durationInFrames={Math.round((totalSeconds-misoSeconds)*fps)} premountFor={fps}><Luna/></Sequence>
    <div style={{position:'absolute',left:112,right:112,top:120,height:1,background:'#C8D1BD'}}/>
    <CaptionLine captions={[
      {text:'And everyday questions can start there, too.',startMs:301,endMs:3100,timestampMs:null,confidence:null},
      {text:'These scripted previews explore food questions and activity records.',startMs:4601,endMs:8900,timestampMs:null,confidence:null},
    ]}/>
    <Footnote>FICTIONAL PRESET SCENARIOS · NO LIVE AI, ACTUAL TRACKING OR DIAGNOSIS</Footnote>
  </Canvas>;
};
