import React from 'react';
import {AbsoluteFill, Composition, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {registerRoot} from 'remotion';

const BG='#07110f';
const PANEL='#0f1f1b';
const TEXT='#f4f7f5';
const MUTED='#a9b7b2';
const GREEN='#b9ff66';
const CYAN='#7fe9ff';
const ORANGE='#ffb36b';
const RED='#ff7b7b';

const box=(extra={})=>({
  background:PANEL,border:'1px solid #24443b',borderRadius:26,padding:34,...extra
});

const Fade=({children,from=0,duration=20})=>{
  const f=useCurrentFrame();
  const o=interpolate(f,[from,from+duration],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  return <div style={{opacity:o}}>{children}</div>;
};

const Title=({eyebrow,title,sub})=>(
  <div style={{maxWidth:1450}}>
    <div style={{fontSize:28,letterSpacing:5,color:GREEN,fontWeight:800,marginBottom:24}}>{eyebrow}</div>
    <div style={{fontSize:94,lineHeight:0.95,letterSpacing:-5,fontWeight:900,color:TEXT}}>{title}</div>
    {sub&&<div style={{fontSize:38,lineHeight:1.25,color:MUTED,marginTop:30,maxWidth:1250}}>{sub}</div>}
  </div>
);

const Scene=({children})=><AbsoluteFill style={{background:BG,color:TEXT,fontFamily:'Inter,Arial,sans-serif',padding:'86px 96px'}}>{children}</AbsoluteFill>;

const Metric=({label,value,accent=GREEN})=>(
  <div style={box({padding:'22px 24px'})}>
    <div style={{fontSize:20,color:MUTED,textTransform:'uppercase',letterSpacing:2}}>{label}</div>
    <div style={{fontSize:42,fontWeight:900,color:accent,marginTop:6}}>{value}</div>
  </div>
);

const Chip=({children,color=CYAN})=><span style={{display:'inline-block',padding:'9px 15px',borderRadius:999,border:`1px solid ${color}`,color,fontSize:22,fontWeight:800,marginRight:10}}>{children}</span>;

const Flow=({items})=>(
  <div style={{display:'flex',alignItems:'center',gap:14,marginTop:46,flexWrap:'wrap'}}>
    {items.map((x,i)=><React.Fragment key={x}><div style={box({padding:'24px 28px',fontSize:28,fontWeight:800,color:i===items.length-1?GREEN:TEXT})}>{x}</div>{i<items.length-1&&<div style={{fontSize:40,color:CYAN}}>→</div>}</React.Fragment>)}
  </div>
);

const Intro=()=>(
  <Scene>
    <Fade>
      <Title eyebrow="OPENCV AI COMPETITION 2026 · AGENTIC VISION" title="ListingLens Agent" sub="An evidence-first catalog-photo QA agent that measures, acts, re-measures, and knows when to ask a human."/>
      <div style={{display:'flex',gap:16,marginTop:54}}>
        <Chip>OpenCV 5.0.0</Chip><Chip color={GREEN}>Agentic Vision</Chip><Chip color={ORANGE}>AWS Lambda + S3</Chip>
      </div>
      <div style={{position:'absolute',left:96,bottom:84,fontSize:26,color:MUTED}}>Ivan Babydov · @williamleewilliam1-star</div>
    </Fade>
  </Scene>
);

const Problem=()=>(
  <Scene>
    <Title eyebrow="THE PROBLEM" title="A quality score is not an action." sub="Marketplace teams need to know: publish, fix automatically, or reshoot — with evidence for every decision."/>
    <Flow items={['PERCEPTION','DECISION','ACTION','RE-PERCEPTION','FINAL DECISION']}/>
    <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:18,marginTop:42}}>
      <Metric label="good frame" value="ACCEPT"/>
      <Metric label="composition only" value="AUTO_CROP" accent={CYAN}/>
      <Metric label="hard failure" value="HUMAN_RESHOOT" accent={ORANGE}/>
    </div>
  </Scene>
);

const Good=()=>(
  <Scene>
    <Title eyebrow="REAL RECORDED EVIDENCE" title="Good input → ACCEPT" sub="OpenCV metrics directly control the next action. No chatbot interpretation is allowed to override hard evidence."/>
    <div style={{display:'grid',gridTemplateColumns:'700px 1fr',gap:44,marginTop:38,alignItems:'center'}}>
      <Img src={staticFile('assets/good-before.png')} style={{width:700,height:560,objectFit:'contain',background:'#fff',borderRadius:24}}/>
      <div style={{display:'grid',gap:16}}>
        <Metric label="sharpness" value="229.58"/>
        <Metric label="mean luminance" value="184.03"/>
        <Metric label="object occupancy" value="0.315"/>
        <div style={box({fontSize:34,fontWeight:900,color:GREEN})}>PERCEPTION → DECISION → NO_CHANGE → ACCEPT</div>
      </div>
    </div>
  </Scene>
);

const AutoCrop=()=>{
  const f=useCurrentFrame();
  const p=interpolate(f,[10,70],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  return <Scene>
    <Title eyebrow="AGENTIC LOOP" title="Composition failure → autonomous crop → re-measure" sub="The crop is not the endpoint. ListingLens re-runs OpenCV and only accepts the corrected image if the second measurement passes."/>
    <div style={{display:'grid',gridTemplateColumns:'1fr 120px 1fr',gap:24,marginTop:34,alignItems:'center'}}>
      <div>
        <div style={{fontSize:26,color:ORANGE,fontWeight:800,marginBottom:12}}>BEFORE</div>
        <Img src={staticFile('assets/margin-before.png')} style={{width:610,height:480,objectFit:'contain',background:'#fff',borderRadius:24}}/>
      </div>
      <div style={{fontSize:70,color:CYAN,textAlign:'center',transform:`scale(${0.8+0.2*p})`}}>→</div>
      <div>
        <div style={{fontSize:26,color:GREEN,fontWeight:800,marginBottom:12}}>AFTER AUTO_CROP</div>
        <Img src={staticFile('assets/margin-after.png')} style={{width:610,height:480,objectFit:'contain',background:'#fff',borderRadius:24}}/>
      </div>
    </div>
    <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:18,marginTop:28}}>
      <Metric label="occupancy" value="0.085 → 0.651" accent={GREEN}/>
      <Metric label="center offset" value="0.266 → 0.000" accent={GREEN}/>
      <Metric label="final decision" value="ACCEPT_AFTER_FIX" accent={GREEN}/>
    </div>
  </Scene>
};

const Failures=()=>(
  <Scene>
    <Title eyebrow="HUMAN CONTROL" title="Some failures should not be “fixed”." sub="Blur and severe exposure failure route to a human. The agent is intentionally bounded."/>
    <div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:24,marginTop:44}}>
      {[
        ['blur-before.png','Blur','sharpness 0.20'],
        ['dark-before.png','Underexposed','shadow clip 30.2%'],
        ['bright-before.png','Overexposed','highlight clip 69.8%']
      ].map(([img,label,metric])=><div key={label} style={box()}>
        <Img src={staticFile('assets/'+img)} style={{width:'100%',height:310,objectFit:'contain',background:'#fff',borderRadius:18}}/>
        <div style={{fontSize:32,fontWeight:900,marginTop:18}}>{label}</div>
        <div style={{fontSize:24,color:MUTED,marginTop:8}}>{metric}</div>
        <div style={{fontSize:27,fontWeight:900,color:ORANGE,marginTop:18}}>HUMAN_RESHOOT</div>
      </div>)}
    </div>
  </Scene>
);

const Aws=()=>(
  <Scene>
    <Title eyebrow="CLOUD DELIVERY" title="The same agent loop is packaged for AWS." sub="S3 is the event/data plane. Lambda runs the OpenCV 5 decision loop and persists an audit JSON plus the corrected image when a bounded crop succeeds."/>
    <Flow items={['S3 incoming/','Lambda container','OpenCV 5 agent','result.json + corrected.png','S3 results/']}/>
    <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:24,marginTop:46}}>
      <div style={box()}>
        <div style={{fontSize:28,color:GREEN,fontWeight:900}}>7/7 TESTS PASS</div>
        <div style={{fontSize:24,color:MUTED,marginTop:12}}>Core policy + fake-S3 Lambda integration</div>
      </div>
      <div style={box({borderColor:'#6e4c25'})}>
        <div style={{fontSize:28,color:ORANGE,fontWeight:900}}>LIVE AWS DEPLOYMENT PENDING</div>
        <div style={{fontSize:24,color:MUTED,marginTop:12}}>This draft does not claim a cloud deployment until a real receipt exists.</div>
      </div>
    </div>
  </Scene>
);

const Results=()=>(
  <Scene>
    <Title eyebrow="EVALUATION" title="5 deterministic cases. 5 expected decisions." sub="The public evidence demo is reproducible and includes both successful autonomy and failure escalation."/>
    <div style={{display:'grid',gridTemplateColumns:'repeat(5,1fr)',gap:14,marginTop:48}}>
      {[
        ['GOOD','ACCEPT',GREEN],
        ['MARGIN','AFTER FIX',CYAN],
        ['BLUR','RESHOT',ORANGE],
        ['DARK','RESHOT',ORANGE],
        ['BRIGHT','RESHOT',ORANGE]
      ].map(([a,b,c])=><div key={a} style={box({textAlign:'center',padding:'34px 18px'})}>
        <div style={{fontSize:24,color:MUTED}}>{a}</div><div style={{fontSize:32,fontWeight:900,color:c,marginTop:14}}>{b}</div>
      </div>)}
    </div>
    <div style={box({marginTop:34,fontSize:30})}>
      <div><b>Public recorded evidence:</b></div>
      <div style={{color:CYAN,marginTop:10}}>williamleewilliam1-star.github.io/babydov-listinglens-agent/</div>
    </div>
  </Scene>
);

const Final=()=>(
  <Scene>
    <Title eyebrow="LISTINGLENS AGENT" title="See → decide → act → verify." sub="OpenCV 5 drives the decision. Automation is bounded. Human escalation is explicit. The evidence stays inspectable."/>
    <div style={{marginTop:60,fontSize:30,color:MUTED,lineHeight:1.6}}>
      <div>Source: github.com/williamleewilliam1-star/babydov-listinglens-agent</div>
      <div>Team: Ivan Babydov</div>
      <div style={{color:GREEN,fontWeight:900,marginTop:22}}>Target: Agentic Vision Award</div>
    </div>
  </Scene>
);

const Video=()=>(
  <AbsoluteFill>
    <Sequence from={0} durationInFrames={210}><Intro/></Sequence>
    <Sequence from={210} durationInFrames={270}><Problem/></Sequence>
    <Sequence from={480} durationInFrames={300}><Good/></Sequence>
    <Sequence from={780} durationInFrames={390}><AutoCrop/></Sequence>
    <Sequence from={1170} durationInFrames={330}><Failures/></Sequence>
    <Sequence from={1500} durationInFrames={330}><Aws/></Sequence>
    <Sequence from={1830} durationInFrames={300}><Results/></Sequence>
    <Sequence from={2130} durationInFrames={270}><Final/></Sequence>
  </AbsoluteFill>
);

const Root=()=> <Composition id="ListingLensJudge" component={Video} durationInFrames={2400} fps={30} width={1920} height={1080}/>;
registerRoot(Root);
