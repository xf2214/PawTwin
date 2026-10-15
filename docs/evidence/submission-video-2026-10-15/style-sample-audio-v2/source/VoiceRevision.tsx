import React from 'react';
import {AbsoluteFill,Sequence,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
import {Audio} from '@remotion/media';
import type {Caption} from '@remotion/captions';
import {Opening} from './Opening';
import {Memory} from './Memory';
import {Context} from './Context';
import {Concierge} from './Concierge';
import {Closing} from './Closing';
import {CaptionLine,LegacyCaptions} from './design';
import plan from './voice-revision-plan.json';
import cues from './voice-revision-captions.json';

const RevisedCaptions=()=>{
  const frame=useCurrentFrame();const {fps}=useVideoConfig();
  const b=plan.boundariesInFrames.map(v=>v/plan.fps*fps);
  if(frame>=b[4])return null; // The closing headline contains the spoken words.
  return <AbsoluteFill style={{fontFamily:'PawBody',pointerEvents:'none'}}><CaptionLine force captions={cues as Caption[]} light={frame>=b[2]&&frame<b[3]}/></AbsoluteFill>;
};

export const VoiceRevision=()=>{
  const {fps}=useVideoConfig();
  const b=plan.boundariesInFrames.map(v=>Math.round(v/plan.fps*fps));
  const end=Math.round(plan.durationSeconds*fps);
  return <AbsoluteFill><LegacyCaptions.Provider value={false}>
    <Sequence name="01 · Meet Mochi" from={0} durationInFrames={b[1]} premountFor={fps}><Opening sampleLabel="FICTIONAL FAMILY STORY · NARRATION & PACING SAMPLE"/></Sequence>
    <Sequence name="02 · Emma remembers the little things" from={b[1]} durationInFrames={b[2]-b[1]} premountFor={fps}><Memory/></Sequence>
    <Sequence name="03 · Alex picks up the same context" from={b[2]} durationInFrames={b[3]-b[2]} premountFor={fps}><Context/></Sequence>
    <Sequence name="04 · Miso and Luna scripted previews" from={b[3]} durationInFrames={b[4]-b[3]} premountFor={fps}><Concierge misoSeconds={plan.misoSeconds} totalSeconds={(b[4]-b[3])/fps}/></Sequence>
    <Sequence name="05 · A relaxed close" from={b[4]} durationInFrames={end-b[4]} premountFor={fps}><Closing/></Sequence>
    <RevisedCaptions/>
    <Audio name="Continuous narration and quiet original music" src={staticFile('soundtrack-v2.stereo.wav')} durationInFrames={end} premountFor={fps}/>
  </LegacyCaptions.Provider></AbsoluteFill>;
};
