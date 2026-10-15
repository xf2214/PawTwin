import React from 'react';
import {AbsoluteFill, CanvasImage, Easing, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {loadFont} from '@remotion/fonts';
import {Video} from '@remotion/media';
import type {Caption} from '@remotion/captions';

export const C = {cream:'#F5F1E8', forest:'#203F35', soft:'#DFE6D5', sage:'#768B69', orange:'#CE8B54', ink:'#243B32'};
export const ready = Promise.all([
  loadFont({family:'PawBody',url:staticFile('body.ttf'),weight:'400'}),
  loadFont({family:'PawBody',url:staticFile('body-semibold.ttf'),weight:'600'}),
  loadFont({family:'PawDisplay',url:staticFile('display.ttf'),weight:'400'}),
]);

export const Reveal: React.FC<{children:React.ReactNode;delay?:number;style?:React.CSSProperties}> = ({children,delay=0,style}) => {
  const f=useCurrentFrame(); const {fps}=useVideoConfig();
  return <div style={{opacity:interpolate(f,[delay*fps,(delay+.4)*fps],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}),translate:interpolate(f,[delay*fps,(delay+.6)*fps],['0px 28px','0px 0px'],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.bezier(.16,1,.3,1)}),...style}}>{children}</div>;
};

export const Brand:React.FC<{light?:boolean;note?:string}> = ({light=false,note}) => <div style={{position:'absolute',left:112,right:112,top:61,display:'flex',alignItems:'center',justifyContent:'space-between',color:light?C.cream:C.forest,fontFamily:'PawBody'}}>
  <div style={{display:'flex',alignItems:'center',gap:15,fontSize:31,fontWeight:600}}><svg width="31" height="35" viewBox="0 0 31 35" fill="currentColor"><ellipse cx="15" cy="24" rx="10" ry="8"/><ellipse cx="4" cy="13" rx="4" ry="5"/><ellipse cx="12" cy="6" rx="4" ry="5"/><ellipse cx="23" cy="8" rx="4" ry="5"/><ellipse cx="29" cy="17" rx="3" ry="4"/></svg>PawTwin</div>
  <div style={{fontSize:20,letterSpacing:2,opacity:.75}}>{note??'A LITTLE MORE UNDERSTANDING'}</div>
</div>;

export const Canvas:React.FC<{children:React.ReactNode;dark?:boolean}> = ({children,dark=false}) => <AbsoluteFill style={{background:dark?C.forest:C.cream,fontFamily:'PawBody',color:dark?C.cream:C.ink,overflow:'hidden'}}>{children}</AbsoluteFill>;

export const Kicker:React.FC<{children:React.ReactNode;style?:React.CSSProperties}> = ({children,style}) => <div style={{fontSize:23,letterSpacing:3.2,fontWeight:600,...style}}>{children}</div>;

export const Pet:React.FC<{name:string;size:number;style?:React.CSSProperties}> = ({name,size,style}) => <Img src={staticFile(`${name}.svg`)} style={{width:size,height:size*1.125,...style}}/>;

export const LegacyCaptions = React.createContext(true);

export const CaptionLine:React.FC<{captions:Caption[];light?:boolean;force?:boolean}> = ({captions,light=false,force=false}) => {
  const enabled=React.useContext(LegacyCaptions);
  const f=useCurrentFrame(); const {fps}=useVideoConfig(); const ms=f/fps*1000;
  const cue=captions.find(c=>ms>=c.startMs&&ms<c.endMs);
  if (!enabled&&!force) return null;
  return <div style={{position:'absolute',left:150,right:150,bottom:70,textAlign:'center',color:light?C.cream:C.forest,fontSize:36,lineHeight:1.3,fontWeight:400,minHeight:48}}>{cue?.text}</div>;
};

export const Footnote:React.FC<{children:React.ReactNode;light?:boolean}> = ({children,light=false}) => <div style={{position:'absolute',left:112,right:112,bottom:23,fontSize:20,letterSpacing:.4,color:light?'#D0D9C9':'#697566',textAlign:'center'}}>{children}</div>;

export const VideoCrop:React.FC<{src:string;crop:[number,number,number,number];sourceSize?:[number,number];x:number;y:number;width:number;radius?:number;hold?:{after:number;src:string}}> = ({src,crop,sourceSize=[1920,1080],x,y,width,radius=25,hold}) => {
  const [cx,cy,cw,ch]=crop; const s=width/cw; const {fps}=useVideoConfig(); const frame=useCurrentFrame();
  const mediaStyle:React.CSSProperties={position:'absolute',left:-cx*s,top:-cy*s,width:sourceSize[0]*s,height:sourceSize[1]*s,maxWidth:'none'};
  return <div style={{position:'absolute',left:x,top:y,width,height:ch*s,overflow:'hidden',borderRadius:radius,background:'#FFF',boxShadow:'0 28px 80px #15352816',outline:'1px solid #BDCCBA70'}}>{hold&&frame>=hold.after*fps?<CanvasImage src={staticFile(hold.src)} style={mediaStyle}/>:<Video name="Actual normal-speed recording" src={staticFile(src)} muted premountFor={fps} style={mediaStyle} />}</div>;
};

export const Picture:React.FC<{src:string;width:number;style?:React.CSSProperties}> = ({src,width,style}) => <CanvasImage src={staticFile(src)} style={{width,height:'auto',...style}}/>;
