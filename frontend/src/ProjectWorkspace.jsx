import React,{useEffect,useState} from 'react';
import CoachMessage from './CoachMessage';
import FeedbackFlag from './FeedbackFlag';
import QuestionHelp from './QuestionHelp';

const labels={not_started:'Not started',in_progress:'Draft saved',needs_revision:'Needs revision',requirements_met:'Requirements met',retry_required:'Retry feedback'};
export default function ProjectWorkspace({request,onLesson,onUpdated}){
 const [data,setData]=useState(null),[selected,setSelected]=useState(null),[text,setText]=useState('');
 const [level,setLevel]=useState('beginner'),[busy,setBusy]=useState(false),[error,setError]=useState(''),[saved,setSaved]=useState('');
 const active=data?.milestones?.find(m=>m.id===selected);
 const pending=active?.pending_submission;
 const dirty=!!active&&text!==active.draft;
 const unchangedFeedback=!!active?.history.some(({attempt})=>attempt.status==='accepted'&&attempt.answer===text);
 function restore(value,id){setData(value);setLevel(value.workspace?.level||value.selected_level||'beginner');
  const next=id||value.workspace?.resume_milestone_id;setSelected(next||null);
  setText(value.milestones?.find(m=>m.id===next)?.draft||'');}
 async function load(){setError('');try{restore(await request('/projects/delivery-time'));}catch(e){setError(e.message);}}
 useEffect(()=>{load();},[]);
 async function start(){setBusy(true);setError('');try{restore(await request('/projects/delivery-time/start',{method:'POST',body:JSON.stringify({level})}));setSaved('');}catch(e){setError(e.message);}finally{setBusy(false);}}
 async function persist(){
  const value=await request(`/projects/delivery-time/${data.workspace.id}/milestones/${active.id}/draft`,{method:'PUT',body:JSON.stringify({text,version:active.draft_version})});
  setData(value);setSaved('Draft saved on this computer.');return value;
 }
 async function save(){setBusy(true);setError('');try{await persist();}catch(e){setError(e.message);}finally{setBusy(false);}}
 async function select(id){if(busy)return;setBusy(true);setError('');try{const value=dirty?await persist():data;restore(value,id);setSaved('');}catch(e){setError(e.message);}finally{setBusy(false);}}
 async function submit(){setBusy(true);setError('');setSaved('');let sent=false;try{
   if(!pending&&dirty)await persist();
   const body=pending?{submission_id:pending.id,answer:pending.attempt.answer}:{submission_id:crypto.randomUUID(),answer:text};
   sent=true;
   restore(await request(`/projects/delivery-time/${data.workspace.id}/milestones/${active.id}/submit`,{method:'POST',body:JSON.stringify(body)}),active.id);
   await onUpdated?.();
  }catch(e){setError(e.message);if(sent){try{const value=await request(`/projects/delivery-time/workspaces/${data.workspace.id}`);restore(value,active.id);}catch{}}}
  finally{setBusy(false);}
 }
 async function cancel(){setBusy(true);setError('');try{await request(`/practice/${pending.attempt.id}/discard`,{method:'POST'});restore(await request(`/projects/delivery-time/workspaces/${data.workspace.id}`),active.id);}catch(e){setError(e.message);}finally{setBusy(false);}}
 const feedback=active?.latest_feedback?.feedback;
 return <><div className="intro"><p className="eyebrow">GUIDED ML PROJECT</p><h1>Build it, one milestone at a time.</h1><p>Save your code, outputs and reasoning. Get feedback, revisit gaps, and resume your saved work.</p></div>
 {error&&<p className="error" role="alert">{error} <button className="secondary" disabled={busy} onClick={load}>Reload saved work</button></p>}
 {!data?<p role="status">Loading project…</p>:<>
 <section className="card project-toolbar"><div><h2>Delivery-time prediction</h2><p>{data.workspace?`${data.workspace.completed} of ${data.workspace.total} milestones meet the rubric requirements at ${data.workspace.level} level.`:'Start a saved workspace for your current level.'}</p></div>
 <label>Project level<select value={level} disabled={busy} onChange={e=>setLevel(e.target.value)}>{data.levels.map(l=><option key={l} value={l}>{l}</option>)}</select></label>
 <button className="primary" disabled={busy||dirty} onClick={start}>{data.workspace?'Open this level':'Start project →'}</button>
 <a className="secondary project-download" href="/api/v1/projects/delivery-time/starter.zip" download>Download starter files</a>
 {dirty&&<p role="status">Unsaved changes. Save before leaving or switching levels.</p>}
 </section>
 {data.workspace&&active&&<div className="project-grid"><nav className="card project-milestones" aria-label="Project milestones">
 {data.milestones.map((m,i)=><button key={m.id} className={m.id===active.id?'selected':''} disabled={busy} onClick={()=>select(m.id)}><strong>{i+1}. {m.title}</strong><span>{labels[m.status]}</span></button>)}
 <p className="fine">You can work in any order. Selecting another milestone saves changes to the current draft.</p></nav>
 <div><section className="card project-work"><span className="tag">{labels[active.status]} · {data.workspace.level}</span><h2>{active.title}</h2>
 <CoachMessage content={active.task}/><h3>Your milestone rubric</h3><ul>{active.rubric.map(c=><li key={c.id}>{c.description}</li>)}</ul>
 <button className="secondary" disabled={busy||dirty} onClick={()=>onLesson({submoduleId:active.related_lesson.submodule_id,moduleId:active.related_lesson.module_id,level:active.related_lesson.level,lessonId:active.related_lesson.id})}>Review the related lesson →</button>
 <label htmlFor="project-draft">Your code, outputs and explanation</label><textarea id="project-draft" rows="14" maxLength="6000" disabled={busy||!!pending} value={pending?.attempt.answer??text} onChange={e=>{setText(e.target.value);setSaved('');}} placeholder="Paste the relevant code or pseudocode, expected/observed outputs, and your reasoning. Keep secrets and credentials out of your submission."/>
 <p className="fine">{text.length}/6000 characters. Drafts stay local. Requesting feedback sends the submitted work and rubric to OpenAI and uses API tokens. The coach does not execute your code.</p>
 <button className="secondary" disabled={busy||!dirty||!!pending} onClick={save}>Save draft</button>
 <button className="primary" disabled={busy||(!pending&&(!text.trim()||unchangedFeedback))} onClick={submit}>{busy?'Working…':pending?'Retry saved submission →':feedback?'Submit revised work →':'Get milestone feedback →'}</button>
 {unchangedFeedback&&!pending&&<p className="fine">This version already has feedback. Edit your work before requesting another evaluation.</p>}
 {pending&&<><p>Your submitted answer is saved unchanged. Retry it, or cancel this pending evaluation before editing and submitting a new version.</p><button className="secondary" disabled={busy} onClick={cancel}>Cancel pending evaluation</button></>}
 {saved&&<p role="status">{saved}</p>}{active.saved_at&&<p className="fine">Last draft save: {new Date(active.saved_at).toLocaleString()}</p>}
 </section>
 {feedback&&<section className="card history"><h2>{feedback.score===null?'Clarify your evidence':`${feedback.score}% of rubric points`}</h2><p><strong>Strengths:</strong> {feedback.strengths}</p><p><strong>What to revisit:</strong> {feedback.gap||'No gap identified in this submission.'}</p>
 {feedback.criteria.map(c=><div className="criterion" key={c.id}><strong>{c.id.replaceAll('_',' ')} · {c.result.replaceAll('_',' ')}</strong>{c.evidence&&<blockquote>{c.evidence}</blockquote>}<p>{c.explanation}</p></div>)}
 <p><strong>Next step:</strong> {feedback.next_step}</p><p>{data.completion_policy}</p>
 <FeedbackFlag key={active.latest_feedback.id} request={request} attemptId={active.latest_feedback.id}/>
 <QuestionHelp key={'help-'+active.latest_feedback.id} request={request} attemptId={active.latest_feedback.id}/>
 <details><summary>Reference approach</summary><CoachMessage content={feedback.reference}/></details>
 </section>}
 {active.history.length>0&&<section className="card history"><h3>Submitted versions</h3>{active.history.map(({submission_id,attempt})=><details key={submission_id}><summary>{new Date(attempt.created_at).toLocaleString()} · {attempt.status==='accepted'?`${attempt.feedback.score??'Unscored'} rubric points`:attempt.status}</summary><pre>{attempt.answer}</pre>{attempt.feedback&&<p>{attempt.feedback.next_step}</p>}</details>)}</section>}
 </div></div>}
 </>}
 </>;
}
