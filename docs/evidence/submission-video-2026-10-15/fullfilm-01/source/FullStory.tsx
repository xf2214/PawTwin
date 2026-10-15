import React from 'react';
import {CanvasImage,interpolate,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
import {Brand,Canvas,C,Footnote,Kicker,Pet,Picture,Reveal} from './design';

export const Handoff=()=> <Canvas dark><Brand light note="A FAMILY HANDOFF"/>
  <Reveal style={{position:'absolute',left:112,top:214,width:950}}><Kicker>TODAY, ALEX IS TAKING OVER.</Kicker><div style={{fontFamily:'PawDisplay',fontSize:106,lineHeight:1.08,marginTop:32}}>What should<br/>Alex know?</div></Reveal>
  <Reveal delay={.15} style={{position:'absolute',left:1260,top:275}}><Pet name="mochi" size={350}/></Reveal>
  <Reveal delay={.5} style={{position:'absolute',left:112,top:700,fontSize:34,color:'#D4DDBE'}}>The little details should stay with the family.</Reveal>
  <Footnote light>FICTIONAL FAMILY STORY · WORKING LOCAL PROTOTYPE</Footnote>
</Canvas>;

export const ContextProof=()=> <Canvas dark><Brand light note="THE SOURCE STAYS VISIBLE"/>
  <Reveal style={{position:'absolute',left:112,top:177,width:650}}><Kicker>02 / A FAMILIAR STARTING POINT</Kicker><div style={{fontFamily:'PawDisplay',fontSize:87,lineHeight:1.1,marginTop:32}}>A source<br/>you can inspect.</div></Reveal>
  <div style={{position:'absolute',left:112,top:495,fontSize:32,lineHeight:1.5,color:'#CAD7BE'}}>The same owner-confirmed<br/>preference, in a fresh chat.</div>
  <Reveal delay={.2} style={{position:'absolute',left:280,top:640}}><Pet name="mochi" size={200}/></Reveal>
  <Picture src="alexa-hold.png" width={958} style={{position:'absolute',left:850,top:165,borderRadius:25}}/>
  <Footnote light>ACTUAL LOCAL UI · ALEXA WEB SIMULATION · LOCAL RULES</Footnote>
</Canvas>;

export const Implementation=()=>{
 const f=useCurrentFrame();const {fps}=useVideoConfig();
 const items=[['Family records','Stored locally in SQLite'],['Answers in this demo','Local rules'],['Alexa experience','Text web simulator']];
 return <Canvas dark><Brand light note="WHAT IS RUNNING TODAY"/>
  <Reveal style={{position:'absolute',left:112,top:203,width:730}}><Kicker>WORKING PROTOTYPE</Kicker><div style={{fontFamily:'PawDisplay',fontSize:94,lineHeight:1.09,marginTop:30}}>Care, with<br/>local context.</div></Reveal>
  {items.map(([title,value],i)=><Reveal key={title} delay={i*2.7+.25} style={{position:'absolute',left:1000,top:218+i*196,width:785,padding:'20px 0',borderBottom:'1px solid #63806B'}}><div style={{fontSize:25,color:'#B9CCAE',letterSpacing:1.4}}>{title.toUpperCase()}</div><div style={{fontSize:43,marginTop:12}}>{value}</div></Reveal>)}
  <div style={{position:'absolute',left:112,top:701,fontSize:30,color:'#BDCEB6',opacity:interpolate(f,[6*fps,6.6*fps],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})}}>Live cloud inference and real Alexa<br/>integration are not demonstrated.</div>
  <Footnote light>LOCAL PROTOTYPE · NO LIVE CLOUD, ALEXA SERVICE OR HARDWARE DEMONSTRATION</Footnote>
 </Canvas>;
};

export const FamilyBenefit=()=> <Canvas dark><Brand light note="ONE SHARED STARTING POINT"/>
  <Reveal style={{position:'absolute',left:112,top:215,fontFamily:'PawDisplay',fontSize:104,lineHeight:1.1}}>One family.<br/><span style={{color:'#D4DDBE'}}>A clearer next step.</span></Reveal>
  <Reveal delay={.15} style={{position:'absolute',left:1370,top:280}}><Pet name="mochi" size={280}/></Reveal>
  <Reveal delay={.5} style={{position:'absolute',left:112,top:647,fontSize:35,color:'#CDDAC2',lineHeight:1.6}}>What Mochi likes. What has been agreed.<br/>What someone has recorded.</Reveal>
  <Footnote light>FICTIONAL FAMILY STORY · CONFIRMED MEMORY · AGREED PLANS · RECORDED CARE</Footnote>
</Canvas>;

export const FilmClosing=()=> <Canvas dark><Brand light note="PAWTWIN"/>
  <Reveal style={{position:'absolute',left:112,top:258,fontFamily:'PawDisplay',fontSize:120,lineHeight:1.12,letterSpacing:-2}}>Less repeating.<br/><span style={{color:'#D4DDBE'}}>More caring.</span></Reveal>
  <Reveal delay={.15} style={{position:'absolute',left:1320,top:304}}><Pet name="mochi" size={325}/></Reveal>
  <div style={{position:'absolute',left:112,top:620,fontSize:31,color:'#C0D0B8'}}>PawTwin · Care, with context.</div>
  <Footnote light>HACKATHON DEMONSTRATION · LOCAL PROTOTYPE + SCRIPTED PRODUCT PREVIEW</Footnote>
</Canvas>;
