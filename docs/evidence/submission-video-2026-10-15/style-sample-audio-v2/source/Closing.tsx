import React from 'react';
import {Brand,Canvas,C,Footnote,Pet,Reveal} from './design';

export const Closing = () => <Canvas dark><Brand light note="ONE SHARED CONTEXT"/>
  <Reveal style={{position:'absolute',left:112,top:258,fontFamily:'PawDisplay',fontSize:120,lineHeight:1.12,letterSpacing:-2}}>Less repeating.<br/><span style={{color:'#D4DDBE'}}>More caring.</span></Reveal>
  <Reveal delay={.15} style={{position:'absolute',left:1320,top:304}}><Pet name="mochi" size={325}/></Reveal>
  <div style={{position:'absolute',left:112,top:620,fontSize:31,color:'#C0D0B8'}}>PawTwin · Care, with context.</div>
  <Footnote light>STYLE SAMPLE · LOCAL PROTOTYPE + SCRIPTED PRODUCT PREVIEW</Footnote>
</Canvas>;
