import React from 'react';
import {Sequence,useVideoConfig} from 'remotion';
import {Brand,Canvas,C,Footnote,Kicker,Pet,Picture,Reveal,VideoCrop} from './design';

const WidePlan:React.FC<{confirm?:boolean}>=({confirm=false})=> <Canvas><Brand note="ALEXA WEB SIMULATION · ACTUAL UI"/>
 <Reveal style={{position:'absolute',left:112,top:143}}><Kicker>03 / {confirm?'EXPLICIT OWNER CONFIRMATION':'REVIEW THE SUGGESTION'}</Kicker><div style={{fontFamily:'PawDisplay',fontSize:69,lineHeight:1.1,marginTop:18}}>{confirm?'Confirm the plan. Then hand it over.':'A draft comes before a commitment.'}</div></Reveal>
 <VideoCrop src={`fullfilm/${confirm?'owner-explicit-confirm':'owner-draft-prepare'}.mp4`} crop={[0,320,1000,400]} sourceSize={[1000,720]} x={160} y={288} width={1600} hold={{after:confirm?10:8,src:`fullfilm/${confirm?'owner-explicit-confirm':'owner-draft-prepare'}-hold.png`}}/>
 <Footnote>EMMA · OWNER · NORMAL-SPEED RECORDING · MANUAL CARE, NOT DEVICE EXECUTION</Footnote>
</Canvas>;
export const DraftPlan=()=> <WidePlan/>;
export const ConfirmPlan=()=> <WidePlan confirm/>;

export const CompleteCare=()=>{
 const {fps}=useVideoConfig();
 return <Canvas dark><Brand light note="ALEX · CARER · ACTUAL UI"/>
  <Reveal style={{position:'absolute',left:112,top:166,width:640}}><Kicker>04 / HAND OFF CLEARLY</Kicker><div style={{fontFamily:'PawDisplay',fontSize:90,lineHeight:1.08,marginTop:30}}>A person<br/>takes over.</div></Reveal>
  <div style={{position:'absolute',left:112,top:475,fontSize:31,lineHeight:1.5,color:'#CAD7BE'}}>Claim the agreed task.<br/>Record the completion.</div>
  <Reveal delay={.15} style={{position:'absolute',left:315,top:650}}><Pet name="mochi" size={170}/></Reveal>
  <Sequence name="Alex claims" durationInFrames={Math.round(2.8*fps)} premountFor={fps}><VideoCrop src="fullfilm/alex-claim-action.mp4" crop={[0,0,736,630]} sourceSize={[736,630]} x={880} y={170} width={890} hold={{after:2.36,src:'fullfilm/alex-claim-action-hold.png'}}/></Sequence>
  <Sequence name="Alex records completion" from={Math.round(2.8*fps)} premountFor={fps}><VideoCrop src="fullfilm/alex-complete-action.mp4" crop={[0,0,736,630]} sourceSize={[736,630]} x={880} y={170} width={890} hold={{after:6.96,src:'fullfilm/alex-complete-action-hold.png'}}/></Sequence>
  <Footnote light>NORMAL-SPEED ACTIONS · WAITING BETWEEN ACTIONS OMITTED · COMPLETION IS A HUMAN RECORD</Footnote>
 </Canvas>;
};

export const RecordedActor=()=> <Canvas dark><Brand light note="A TRACEABLE HOUSEHOLD RECORD"/>
 <Reveal style={{position:'absolute',left:112,top:195,width:660}}><Kicker>04 / THE SAVED RESULT</Kicker><div style={{fontFamily:'PawDisplay',fontSize:88,lineHeight:1.1,marginTop:28}}>Know who<br/>recorded it.</div></Reveal>
 <div style={{position:'absolute',left:112,top:518,fontSize:32,lineHeight:1.5,color:'#CAD7BE'}}>Alex's account is attached<br/>to the household history.</div>
 <Picture src="fullfilm/alex-history-attribution.png" width={1020} style={{position:'absolute',left:790,top:282,borderRadius:25}}/>
 <Footnote light>ACTUAL LOCAL HOUSEHOLD ACTIVITY · RECORDED COMPLETION, NOT PHYSICAL VERIFICATION</Footnote>
</Canvas>;

export const DailyReport=()=> <Canvas><Brand note="EMMA · OWNER · ACTUAL UI"/>
 <Reveal style={{position:'absolute',left:112,top:157,width:650}}><Kicker>05 / CLOSE THE LOOP</Kicker><div style={{fontFamily:'PawDisplay',fontSize:88,lineHeight:1.08,marginTop:30}}>The result<br/>comes home.</div></Reveal>
 <div style={{position:'absolute',left:112,top:480,fontSize:32,lineHeight:1.5,color:C.sage}}>A report of saved records,<br/>with missing data left visible.</div>
 <VideoCrop src="fullfilm/emma-daily-report-v2.mp4" crop={[0,0,1100,734]} sourceSize={[1100,734]} x={775} y={232} width={1033} hold={{after:7,src:'fullfilm/emma-daily-report-v2-hold.png'}}/>
 <Footnote>NORMAL-SPEED RECORDING · GENERATED DAILY REPORT · NO HEALTH OUTCOME INFERRED</Footnote>
</Canvas>;

export const ReportProof=()=> <Canvas><Brand note="ONE SAVED CARE RECORD"/>
 <Reveal style={{position:'absolute',left:112,top:164}}><Kicker>05 / A SHARED VIEW</Kicker><div style={{fontFamily:'PawDisplay',fontSize:79,lineHeight:1.1,marginTop:25}}>Recorded care, with its limits visible.</div></Reveal>
 <div style={{position:'absolute',left:160,top:340,width:1600,height:515,overflow:'hidden',borderRadius:25,boxShadow:'0 25px 70px #173E2A12'}}><Picture src="fullfilm/emma-daily-report-v2-hold.png" width={1600} style={{position:'absolute',top:-380/1100*1600,left:0}}/></div>
 <Footnote>ACTUAL DAILY REPORT · SAVED HOUSEHOLD RECORDS DO NOT VERIFY PHYSICAL CARE</Footnote>
</Canvas>;
