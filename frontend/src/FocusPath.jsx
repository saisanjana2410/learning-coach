import React from 'react';

export default function FocusPath({catalog,onLesson,onPractice,onProject}){
 const focus=catalog.focus;
 if(!focus)return null;
 const topics=focus.module_ids.map(id=>catalog.modules.find(m=>m.id===id)).filter(Boolean)
   .map(m=>({module:m,topic:m.submodules.find(s=>s.release_focus)})).filter(x=>x.topic);
 return <section className="card focus-path">
  <span className="eyebrow">CURRENT RELEASE</span><h2>{focus.title}</h2><p>{focus.description}</p>
  <div className="focus-steps">{topics.map(({module:m,topic:s},i)=><div key={s.id}>
   <span className="tag">STEP {i+1} · {s.level}</span><h3>{s.title}</h3>
   <p>{s.lessons[0]?.title}</p>
   {s.lessons.map(l=><button className="primary" key={l.id} onClick={()=>onLesson({submoduleId:s.id,moduleId:m.id,level:s.level,lessonId:l.id})}>Start lesson →</button>)}
   <button className="secondary" onClick={()=>onPractice(null,'concept',s.id,s.level)}>Practice →</button>
  </div>)}</div>
  <button className="primary" onClick={onProject}>Open saved project workspace →</button>
  <details><summary>Guided project milestones and starter files</summary>
   <p>Build a delivery-time prediction service locally. This kit uses synthetic data and makes no external API calls.</p>
   <ol>{focus.milestones.map(step=><li key={step}>{step}</li>)}</ol>
   <a className="primary project-download" href={focus.project_download} download>Download runnable project kit</a>
   <p className="fine">The kit includes training, a prediction API, dependencies and setup instructions. Milestones are a checklist, not automatic completion claims. Submit your work in applied practice for feedback.</p>
  </details>
 </section>;
}
