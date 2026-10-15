import React from 'react';
import {AbsoluteFill,Sequence,staticFile,useVideoConfig} from 'remotion';
import {Audio} from '@remotion/media';
import {Opening} from './Opening';
import {Memory} from './Memory';
import {Context} from './Context';
import {Concierge} from './Concierge';
import {Closing} from './Closing';

export const Sample = () => {
  const {fps}=useVideoConfig();
  return <AbsoluteFill>
    <Sequence name="01 · Care feels familiar" from={0} durationInFrames={4.2*fps} premountFor={fps}><Opening/></Sequence>
    <Sequence name="02 · Emma confirms a memory" from={4.2*fps} durationInFrames={6.3*fps} premountFor={fps}><Memory/></Sequence>
    <Sequence name="03 · Alex's fresh conversation" from={10.5*fps} durationInFrames={5.8*fps} premountFor={fps}><Context/></Sequence>
    <Sequence name="04 · Scripted concierge preview" from={16.3*fps} durationInFrames={10.7*fps} premountFor={fps}><Concierge/></Sequence>
    <Sequence name="05 · More caring" from={27*fps} durationInFrames={3*fps} premountFor={fps}><Closing/></Sequence>
    <Audio name="Narration and original music" src={staticFile('final-soundtrack.wav')} durationInFrames={30*fps} premountFor={fps}/>
  </AbsoluteFill>;
};
