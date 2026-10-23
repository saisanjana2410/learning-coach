import React, { useEffect, useState } from 'react';
import CoachMessage from './CoachMessage';
import QuestionHelp from './QuestionHelp';
import { RunSummary } from './PracticeFlow';

export function ProgressView({ request, onPractice }) {
  const [history,setHistory]=useState([]);
  const [data,setData]=useState(null); const [error,setError]=useState('');
  async function load(){try{setError('');const [p,h]=await Promise.all([request('/progress'),request('/runs/history')]);setData(p);setHistory(h);}catch(e){setError(e.message);}}
  useEffect(()=>{load();},[]);
  return <><div className="intro"><p className="eyebrow">YOUR PROGRESS</p><h1>Turn feedback into progress.</h1><p>Evidence across practice and interview answers, with revision dates to help you return.</p></div>{error ? <p role="alert">{error} <button onClick={load}>Retry</button></p> : !data ? <p role="status">Loading progress…</p> : <>
    <section className="card"><h2>Skills and review dates</h2><p>Scores are rubric feedback, not a measure of interview readiness. Unassessed skills are not weak areas.</p>{!data.skills.length && <p>No assessed skills yet. Complete a practice question to begin.</p>}{data.skills.map(s=><div className="progress-row" key={s.skill+s.mode}><div><strong>{s.skill}</strong><p>{s.dimension} · {s.status.replaceAll('_',' ')} · {s.evidence_count} attempt(s)</p>{s.gap && <p>{s.gap}</p>}<small>{s.reason}</small></div><div><span className="pill">{s.score}%</span><p>{s.due ? 'Due now' : 'Review'} · {new Date(s.due_at).toLocaleDateString()}</p><button onClick={()=>onPractice(s.skill,s.mode)}>Practice this skill →</button></div></div>)}</section>
    <section className="card history"><h2>Recent feedback</h2>{!data.recent_attempts.length && <p>Your assessed answers will appear here.</p>}{data.recent_attempts.map(a=><details key={a.id}><summary>{a.question.skill} · {a.mode} · {a.feedback.score === null ? 'Needs clarification' : `${a.feedback.score}%`}</summary><p>{a.question.prompt}</p><CoachMessage content={a.answer}/><p><strong>Feedback:</strong> {a.feedback.gap || a.feedback.strengths}</p><p><strong>Next:</strong> {a.feedback.next_step}</p><QuestionHelp request={request} attemptId={a.id}/></details>)}</section>
    {history.map(value=><details className="card history" key={value.run.id}><summary>Session summary · {value.run.scope==='role'?value.run.role:'Linear regression'} · {new Date(value.summary.finished_at).toLocaleDateString()}</summary><RunSummary value={value} request={request}/></details>)}
  </>}</>;
}
