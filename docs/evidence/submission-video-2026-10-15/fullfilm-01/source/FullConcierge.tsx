import React from 'react';
import {Brand,Canvas,C,Footnote,Kicker,Picture,Reveal} from './design';
import {Miso,Luna} from './Concierge';

export const MisoPreview=()=> <Canvas><Brand note="SCRIPTED PET CONCIERGE PREVIEW"/><Miso/><Footnote>FICTIONAL PRESET SCENARIO · NO LIVE MODEL RESPONSE, TRACKING OR DIAGNOSIS</Footnote></Canvas>;
export const LunaPreview=()=> <Canvas><Brand note="SCRIPTED PET CONCIERGE PREVIEW"/><Luna/><Footnote>ILLUSTRATIVE ACTIVITY RECORDS · PRESET RESPONSE · NOT TRACKING OR A DIAGNOSIS</Footnote></Canvas>;
export const PreviewBoundary=()=> <Canvas><Brand note="SCRIPTED PRODUCT PREVIEW"/>
 <Reveal style={{position:'absolute',left:112,top:151}}><Kicker>THE IDEA / LESS REPEATED BACKGROUND</Kicker><div style={{fontFamily:'PawDisplay',fontSize:74,lineHeight:1.1,marginTop:22}}>Keep the relevant context alongside the question.</div></Reveal>
 <Reveal delay={.15} style={{position:'absolute',left:112,top:336}}><Picture src="05-context-new-chat@2x.png" width={794} style={{borderRadius:25}}/></Reveal>
 <Reveal delay={.5} style={{position:'absolute',left:1006,top:336}}><Picture src="05-context-included@2x.png" width={794} style={{borderRadius:25}}/></Reveal>
 <div style={{position:'absolute',left:112,top:842,fontSize:28,color:C.sage}}>Preset comparison · product direction, not a live inference test.</div>
 <Footnote>FICTIONAL PRESET CONVERSATIONS AND TRACES · NO LIVE AI, ACTUAL TRACKING OR DIAGNOSIS</Footnote>
</Canvas>;
