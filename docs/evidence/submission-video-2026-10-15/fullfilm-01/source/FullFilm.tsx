import React from 'react';
import {AbsoluteFill,Sequence,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
import {Audio} from '@remotion/media';
import type {Caption} from '@remotion/captions';
import {Opening} from './Opening';
import {Memory} from './Memory';
import {Context} from './Context';
import {CaptionLine,LegacyCaptions} from './design';
import {Handoff,ContextProof,Implementation,FamilyBenefit,FilmClosing} from './FullStory';
import {DraftPlan,ConfirmPlan,CompleteCare,RecordedActor,DailyReport,ReportProof} from './FullWorkflow';
import {MisoPreview,LunaPreview,PreviewBoundary} from './FullConcierge';
import plan from './fullfilm-plan.json';
import captions from './fullfilm-captions.json';

const NarrationCaptions=()=>{
 const f=useCurrentFrame();const {fps}=useVideoConfig();const b=plan.boundaries;
 const sourceFrame=f/fps*plan.fps;
 if(sourceFrame>=b.closing)return null; // The end card itself carries every spoken closing word.
 const dark=(sourceFrame>=b.handoff&&sourceFrame<b.memory)||(sourceFrame>=b.context&&sourceFrame<b.draft)||(sourceFrame>=b.complete&&sourceFrame<b.report)||(sourceFrame>=b.implementation);
 return <AbsoluteFill style={{fontFamily:'PawBody',pointerEvents:'none'}}><CaptionLine force captions={captions as Caption[]} light={dark}/></AbsoluteFill>;
};

export const FullFilm=()=>{
 const {fps}=useVideoConfig();const b=plan.boundaries;const t=(n:number)=>Math.round(n/plan.fps*fps);const end=t(plan.durationInFrames);
 return <AbsoluteFill><LegacyCaptions.Provider value={false}>
  <Sequence name="01 · Meet Mochi" durationInFrames={t(b.handoff)} premountFor={fps}><Opening sampleLabel="FICTIONAL FAMILY STORY · WORKING LOCAL PROTOTYPE"/></Sequence>
  <Sequence name="02 · Alex is taking over" from={t(b.handoff)} durationInFrames={t(b.memory-b.handoff)} premountFor={fps}><Handoff/></Sequence>
  <Sequence name="03 · Emma confirms a memory" from={t(b.memory)} durationInFrames={t(b.context-b.memory)} premountFor={fps}><Memory playAfter={plan.memoryPlayAfter}/></Sequence>
  <Sequence name="04 · A genuinely fresh conversation" from={t(b.context)} durationInFrames={t(b.proof-b.context)} premountFor={fps}><Context/></Sequence>
  <Sequence name="05 · Inspect the confirmed source" from={t(b.proof)} durationInFrames={t(b.draft-b.proof)} premountFor={fps}><ContextProof/></Sequence>
  <Sequence name="06 · Review a draft and prepare proposal" from={t(b.draft)} durationInFrames={t(b.confirm-b.draft)} premountFor={fps}><DraftPlan/></Sequence>
  <Sequence name="07 · Explicitly confirm manual care" from={t(b.confirm)} durationInFrames={t(b.complete-b.confirm)} premountFor={fps}><ConfirmPlan/></Sequence>
  <Sequence name="08 · Claim and record completion" from={t(b.complete)} durationInFrames={t(b.historyShot-b.complete)} premountFor={fps}><CompleteCare/></Sequence>
  <Sequence name="09 · The recorded actor" from={t(b.historyShot)} durationInFrames={t(b.report-b.historyShot)} premountFor={fps}><RecordedActor/></Sequence>
  <Sequence name="10 · Generate the actual daily report" from={t(b.report)} durationInFrames={Math.round(7.5*fps)} premountFor={fps}><DailyReport/></Sequence>
  <Sequence name="11 · Read the reported result" from={t(b.report)+Math.round(7.5*fps)} durationInFrames={t(b.concierge-b.report)-Math.round(7.5*fps)} premountFor={fps}><ReportProof/></Sequence>
  <Sequence name="12 · Miso scripted food question" from={t(b.concierge)} durationInFrames={t(b.luna-b.concierge)} premountFor={fps}><MisoPreview/></Sequence>
  <Sequence name="13 · Luna illustrative activity" from={t(b.luna)} durationInFrames={t(b.preset-b.luna)} premountFor={fps}><LunaPreview/></Sequence>
  <Sequence name="14 · Preset comparison and boundaries" from={t(b.preset)} durationInFrames={t(b.implementation-b.preset)} premountFor={fps}><PreviewBoundary/></Sequence>
  <Sequence name="15 · What runs locally" from={t(b.implementation)} durationInFrames={t(b.benefit-b.implementation)} premountFor={fps}><Implementation/></Sequence>
  <Sequence name="16 · A clearer next step" from={t(b.benefit)} durationInFrames={t(b.closing-b.benefit)} premountFor={fps}><FamilyBenefit/></Sequence>
  <Sequence name="17 · PawTwin" from={t(b.closing)} durationInFrames={end-t(b.closing)} premountFor={fps}><FilmClosing/></Sequence>
  <NarrationCaptions/>
  <Audio name="Continuous English narration and original music" src={staticFile('fullfilm/soundtrack.stereo.wav')} durationInFrames={end} premountFor={fps}/>
 </LegacyCaptions.Provider></AbsoluteFill>;
};
