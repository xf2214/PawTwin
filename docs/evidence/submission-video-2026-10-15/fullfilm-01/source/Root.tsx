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
import {FullFilm} from './FullFilm';
import fullFilmPlan from './fullfilm-plan.json';
import {DraftPlan,ConfirmPlan,CompleteCare,DailyReport} from './FullWorkflow';

export const Root = () => <>
  <Composition id="PawTwinStyleSample" component={Sample} width={1920} height={1080} fps={30} durationInFrames={900}/>
  <Composition id="PawTwinVoiceRevision" component={VoiceRevision} width={1920} height={1080} fps={30} durationInFrames={revisionPlan.durationInFrames}/>
  <Composition id="PawTwinHackathonFilm" component={FullFilm} width={1920} height={1080} fps={30} durationInFrames={fullFilmPlan.durationInFrames}/>
  <Folder name="FullFilmScenes">
    <Composition id="DraftPlan" component={DraftPlan} width={1920} height={1080} fps={30} durationInFrames={248}/>
    <Composition id="ConfirmPlan" component={ConfirmPlan} width={1920} height={1080} fps={30} durationInFrames={309}/>
    <Composition id="CompleteCare" component={CompleteCare} width={1920} height={1080} fps={30} durationInFrames={321}/>
    <Composition id="DailyReport" component={DailyReport} width={1920} height={1080} fps={30} durationInFrames={225}/>
  </Folder>
  <Folder name="Scenes">
    <Composition id="Opening" component={Opening} width={1920} height={1080} fps={30} durationInFrames={126}/>
    <Composition id="OwnerMemory" component={Memory} width={1920} height={1080} fps={30} durationInFrames={189}/>
    <Composition id="FreshContext" component={Context} width={1920} height={1080} fps={30} durationInFrames={174}/>
    <Composition id="ConciergePreview" component={Concierge} width={1920} height={1080} fps={30} durationInFrames={321}/>
    <Composition id="Closing" component={Closing} width={1920} height={1080} fps={30} durationInFrames={90}/>
  </Folder>
</>;
