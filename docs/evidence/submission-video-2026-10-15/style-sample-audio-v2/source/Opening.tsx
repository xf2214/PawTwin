import React from 'react';
import {interpolate,useCurrentFrame,useVideoConfig} from 'remotion';
import {Brand,Canvas,CaptionLine,C,Footnote,Kicker,Pet,Reveal} from './design';

export const Opening:React.FC<{sampleLabel?:string}> = ({sampleLabel='FICTIONAL FAMILY STORY · 30-SECOND STYLE SAMPLE'}) => {
  const frame=useCurrentFrame(); const {fps}=useVideoConfig();
  return <Canvas><Brand note="CARE, WITH CONTEXT"/>
    <div style={{position:'absolute',left:1080,top:166,width:690,height:690,borderRadius:'50%',background:C.soft}}/>
    <svg style={{position:'absolute',left:1040,top:180,width:780,height:660}} viewBox="0 0 780 660"><path d="M90 340C30 40 730 0 690 340S30 650 90 340" stroke="#9DAF8F" strokeWidth="2" strokeDasharray="8 12" fill="none"/></svg>
    <Reveal style={{position:'absolute',left:112,top:224}}><Kicker>ONE PET. A SHARED ROUTINE.</Kicker><div style={{fontFamily:'PawDisplay',fontSize:118,lineHeight:1.08,letterSpacing:-3,marginTop:30}}>Care feels<br/><span style={{color:C.sage}}>more familiar.</span></div></Reveal>
    <Reveal delay={.3} style={{position:'absolute',left:1220,top:275}}><Pet name="mochi" size={400}/></Reveal>
    <Reveal delay={.55} style={{position:'absolute',left:1060,top:666,background:'#FFFDFA',borderRadius:22,padding:'20px 28px',boxShadow:'0 18px 50px #29453610',fontSize:30}}>Mochi <span style={{color:'#78816E'}}>·</span> Emma + Alex</Reveal>
    <div style={{position:'absolute',left:112,top:730,width:interpolate(frame,[.65*fps,1.65*fps],[0,545],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}),height:3,background:C.orange}}/>
    <CaptionLine captions={[{text:'Care feels easier when everyone knows your pet.',startMs:501,endMs:3300,timestampMs:null,confidence:null}]}/>
    <Footnote>{sampleLabel}</Footnote>
  </Canvas>;
};
