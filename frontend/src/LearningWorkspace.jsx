import React, { useEffect, useState } from 'react';
import CoachMessage from './CoachMessage';
import 'katex/dist/katex.min.css';

export default function LearningWorkspace({ request, initialSession, onSession, onPractice, selection, onBack }) {
  const [lessons, setLessons] = useState([]);
  const [session, setSession] = useState(null);
  const [status, setStatus] = useState(null);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [pending, setPending] = useState(null);
  const [loading, setLoading] = useState(true);

  async function initialize() {
    setLoading(true); setError('');
    try {
      const [content, tutor] = await Promise.all([request(selection ? `/lessons?submodule_id=${encodeURIComponent(selection.submoduleId)}&level=${selection.level}` : '/lessons'), request('/tutor/status')]);
      setLessons(content); setStatus(tutor);
      if (selection?.lessonId) {
        const existing=initialSession ? await request(`/sessions/${initialSession.id}`) : null;
        if(existing?.lesson_id===selection.lessonId) restore(existing);
        else restore(await request('/sessions',{method:'POST',body:JSON.stringify({lesson_id:selection.lessonId})}));
      } else if (initialSession) restore(await request(`/sessions/${initialSession.id}`));
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  }
  function restore(value) {
    setSession(value);
    onSession?.({id:value.id, lesson_id:value.lesson_id});
    const unanswered = value.messages.find(m => m.role === 'user' && !value.messages.some(r => r.reply_to === m.id));
    setPending(unanswered ? {client_message_id: unanswered.id, text: unanswered.content} : null);
  }
  useEffect(() => { initialize(); }, []);
  async function start(lesson) {
    setBusy(true); setError('');
    try { restore(await request('/sessions', {method:'POST', body:JSON.stringify({lesson_id:lesson.id})})); }
    catch(e) { setError(e.message); } finally { setBusy(false); }
  }
  async function send(e) {
    e.preventDefault();
    const message = pending || {client_message_id: crypto.randomUUID(), text:text.trim()};
    if (!message.text || busy) return;
    setPending(message); setBusy(true); setError('');
    try {
      restore(await request(`/sessions/${session.id}/messages`, {method:'POST', body:JSON.stringify(message)}));
      setText('');
    } catch(e) { setError(e.message); } finally { setBusy(false); }
  }
  return <><button className="secondary submodule-back" onClick={()=>onBack?.(session?.lesson.submodule_id||selection?.submoduleId)}>← Back to submodule</button><div className="intro"><p className="eyebrow">{session?.lesson.module_id?.toUpperCase() || 'LEARNING'} · {session?.lesson.level || selection?.level || 'beginner'} · LEARN MODE</p><h1>Start with understanding.</h1><p>Read a short lesson, explore an example, and ask your tutor a question.</p></div>
    {loading ? <p role="status">Loading lessons…</p> : <>
      {!lessons.length && <button onClick={initialize}>Retry loading lessons</button>}
      <div className="lesson-tabs" aria-label="Lessons">{lessons.map((l,i) => <button key={l.id} disabled={busy} className={session?.lesson_id === l.id ? 'active' : ''} onClick={() => start(l)}><small>LESSON {i+1} · {l.minutes} MIN</small>{l.title}</button>)}</div>
      {!session ? <section className="card"><h2>Choose a lesson to begin</h2><p>Lessons are available without an API key. Your learning conversation is saved when you use the tutor.</p></section> : <div className="learning-grid">
        <article className="card lesson"><span className="tag">{session.lesson.skill}</span><h2>{session.lesson.title}</h2>{session.lesson.sections.filter(s=>!["Guided exercise","Independent challenge"].includes(s.heading)).map(section => <section key={section.heading}><h3>{section.heading}</h3><p>{section.text}</p></section>)}{session.lesson.runnable_code&&<section><h3>Run the example</h3><p>Run this in your local Python 3 interpreter. Code is not executed by this app.</p><pre><code>{session.lesson.runnable_code}</code></pre><h4>Expected output</h4><pre><code>{session.lesson.expected_output}</code></pre></section>}{session.lesson.sections.filter(s=>["Guided exercise","Independent challenge"].includes(s.heading)).map(section=><section key={section.heading}><h3>{section.heading}</h3><p>{section.text}</p></section>)}{session.lesson.mini_project&&<section><h3>{session.lesson.mini_project.title}</h3><p>{session.lesson.mini_project.task}</p><h4>What your feedback will assess</h4><ul>{session.lesson.mini_project.rubric.map(r=><li key={r.criterion}>{r.description}</li>)}</ul><p>Submit your code and reasoning through applied practice. The coach reviews your answer; it does not run your code.</p><button className="secondary" onClick={()=>onPractice(session.lesson.skill,'applied',session.lesson.submodule_id)}>Submit mini-project →</button></section>}{session.lesson.further_reading?.length>0&&<section><h3>Further reading</h3><ul>{session.lesson.further_reading.map(r=><li key={r.url}><a href={r.url} target="_blank" rel="noreferrer">{r.title}</a></li>)}</ul></section>}{session.lesson.next_topic_ids?.length>0&&<section><h3>Continue your learning</h3><p>Suggested next topics; availability and prerequisites are shown in Modules.</p>{session.lesson.next_topic_ids.map(id=><button className="secondary" key={id} onClick={()=>onBack?.(id)}>{id.replaceAll('-',' ')} →</button>)}</section>}<div className="takeaway"><strong>Remember</strong><p>{session.lesson.takeaway}</p><button className="primary" onClick={()=>onPractice(session.lesson.skill,'concept',session.lesson.submodule_id)}>Practice this concept →</button><button className="secondary" onClick={()=>onPractice(session.lesson.skill,'applied',session.lesson.submodule_id)}>Apply this concept →</button></div></article>
        <section className="card tutor"><span className="eyebrow">YOUR LEARNING COMPANION</span><h2>Talk it through.</h2><p>Ask for another example or explain the idea in your own words. This conversation isn’t a scored assessment.</p>
          {status?.configured ? <p className="connection">● Tutor configured · OpenAI</p> : <p className="setup-note">To enable the tutor, add your key to <code>backend/.env</code> and restart the backend. Keep reading in the meantime.</p>}
          <div className="messages" role="log" aria-live="polite">{session.messages.length === 0 && <p className="chat-empty">Try: “Explain this concept with a different example.”</p>}{session.messages.map(m => <div key={m.id} className={`message ${m.role}`}><strong className="message-author">{m.role === 'user' ? 'You' : 'Learning Coach'}</strong>{m.role === 'assistant' ? <CoachMessage content={m.content}/> : <p>{m.content}</p>}</div>)}</div>
          {busy && <p role="status">Working on your request…</p>}
          {error && <p className="error" role="alert">{error}</p>}
          <form onSubmit={send}><label htmlFor="tutor-question">Your question or explanation</label><textarea id="tutor-question" rows="4" maxLength="4000" value={pending?.text || text} disabled={busy || !!pending} onChange={e => setText(e.target.value)} placeholder="What would you like to understand?"/><button className="primary" disabled={busy || !status?.configured || (!pending && !text.trim())}>{busy ? 'Thinking…' : pending ? 'Retry saved message →' : 'Ask tutor →'}</button></form>
          <p className="fine">Messages are saved locally. Recent conversation and learning context are sent to OpenAI when you ask the tutor.</p>
        </section>
      </div>}
      {error && !session && <p role="alert" className="error">{error}</p>}
    </>}
  </>;
}
