import React from 'react';
import {interpolate,useCurrentFrame,useVideoConfig} from 'remotion';
import {Brand,Canvas,CaptionLine,C,Footnote,Kicker,Pet,Reveal,VideoCrop} from './design';

export const Memory = () => {
  const frame=useCurrentFrame(); const {fps}=useVideoConfig();
  const transfer=interpolate(frame,[4.45*fps,5.7*fps],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  return <Canvas><Brand note="WORKING LOCAL PROTOTYPE"/>
  <Reveal style={{position:'absolute',left:112,top:155,width:640}}><Kicker>01 / OWNER CONTROL</Kicker><div style={{fontFamily:'PawDisplay',fontSize:91,lineHeight:1.08,letterSpacing:-2,marginTop:30}}>Only what<br/>you confirm.</div></Reveal>
  <div style={{position:'absolute',right:112,top:155,padding:'15px 25px',border:'1px solid #B6C3AD',borderRadius:30,fontSize:26}}>Emma · Owner</div>
  <Reveal delay={.05}><VideoCrop src="memory-crop.mp4" crop={[0,1,475,275]} sourceSize={[476,276]} x={850} y={330} width={958} hold={{after:6.3,src:'memory-hold.png'}}/></Reveal>
  <div style={{position:'absolute',left:850,top:269,color:C.sage,fontSize:25,letterSpacing:1.5}}>MOCHI’S SHARED MEMORY · ACTUAL UI</div>
  <Reveal delay={.2} style={{position:'absolute',left:222,top:460}}><Pet name="mochi" size={245}/></Reveal>
  <svg style={{position:'absolute',left:112,top:805,width:548,height:90}} viewBox="0 0 468 90"><path d="M58 33H408" stroke="#CBD4C0" strokeWidth="2"/><path d="M58 33H408" stroke={C.sage} strokeWidth="4" strokeDasharray="350" strokeDashoffset={350*(1-transfer)}/><circle cx="40" cy="33" r="28" fill={C.forest}/><text x="40" y="43" textAnchor="middle" fontFamily="PawBody" fontSize="28" fill={C.cream}>E</text><g opacity={.25+.75*transfer}><circle cx="430" cy="33" r="28" fill={C.forest}/><text x="430" y="43" textAnchor="middle" fontFamily="PawBody" fontSize="28" fill={C.cream}>A</text></g><text x="40" y="83" textAnchor="middle" fontFamily="PawBody" fontSize="21" fill={C.forest}>Emma</text><text x="430" y="83" textAnchor="middle" fontFamily="PawBody" fontSize="21" fill={C.forest}>Alex</text></svg>
  <CaptionLine captions={[{text:'Emma confirms what Mochi loves.',startMs:301,endMs:3000,timestampMs:null,confidence:null}]}/>
  <Footnote>LOCAL ACCOUNT · SQLITE MEMORY · NORMAL-SPEED RECORDING</Footnote>
</Canvas>;
};
