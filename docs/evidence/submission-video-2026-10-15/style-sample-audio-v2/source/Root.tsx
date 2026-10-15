import React from 'react';
import {Composition,Folder} from 'remotion';
import {Sample} from './Sample';
import {Opening} from './Opening';
import {Memory} from './Memory';
import {Context} from './Context';
import {Concierge} from './Concierge';
import {Closing} from './Closing';
import {VoiceRevision} from './VoiceRevision';
import revisionPlan from './voice-revision-plan.json';

export const Root = () => <>
  <Composition id="PawTwinStyleSample" component={Sample} width={1920} height={1080} fps={30} durationInFrames={900}/>
  <Composition id="PawTwinVoiceRevision" component={VoiceRevision} width={1920} height={1080} fps={30} durationInFrames={revisionPlan.durationInFrames}/>
  <Folder name="Scenes">
    <Composition id="Opening" component={Opening} width={1920} height={1080} fps={30} durationInFrames={126}/>
    <Composition id="OwnerMemory" component={Memory} width={1920} height={1080} fps={30} durationInFrames={189}/>
    <Composition id="FreshContext" component={Context} width={1920} height={1080} fps={30} durationInFrames={174}/>
    <Composition id="ConciergePreview" component={Concierge} width={1920} height={1080} fps={30} durationInFrames={321}/>
    <Composition id="Closing" component={Closing} width={1920} height={1080} fps={30} durationInFrames={90}/>
  </Folder>
</>;
