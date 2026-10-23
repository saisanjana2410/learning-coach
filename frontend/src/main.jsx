import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';
import LearningWorkspace from './LearningWorkspace';
import PracticeWorkspace, { ProgressView } from './PracticeWorkspace';

async function request(path, options = {}) {
  const response = await fetch(`/api/v1${path}`, { ...options, headers: { 'Content-Type': 'application/json' } });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(Array.isArray(body.detail) ? body.detail.map(e => e.msg).join('. ') : typeof body.detail === 'string' ? body.detail : 'Could not reach the learning service. Please try again.');
  }
  return response.json();
}

function App() {
  const [data, setData] = useState(null);
  const [view, setView] = useState('dashboard');
  const [selection, setSelection] = useState(null);
  const practice = (skill=null, mode='concept') => {setSelection({skill,mode});setView('practice');};
  const refreshProgress = async () => setData(await request('/dashboard'));
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  async function load() {
    setLoading(true); setError('');
    try { setData(await request('/dashboard')); } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);
  return <div className="shell">
    <aside><a className="brand" href="#" onClick={() => setView('dashboard')}><span className="brand-mark">L</span> Learning Coach</a><p className="aside-label">YOUR WORKSPACE</p><nav aria-label="Main navigation">{[['dashboard','Overview'],['learn','Learn'],['practice','Practice'],['progress','Your progress'],['settings','Learning profile']].map(([id,label]) => <button key={id} className={view === id ? 'selected' : ''} onClick={() => setView(id)}>{label}<span>↗</span></button>)}</nav><div className="aside-bottom"><span className="dot"/> A little progress, every day.<p>Your learning journey starts here.</p></div></aside>
    <main><header><span>PERSONAL LEARNING WORKSPACE</span><span className="pill">Foundation · v0.1</span></header>
      {loading ? <p role="status">Loading your workspace…</p> : error && !data ? <section className="card"><p role="alert">{error}</p><button onClick={load}>Try again</button></section> : !data?.profile || view === 'settings' ? <ProfileForm profile={data?.profile} onSaved={async () => { await load(); setView('dashboard'); }}/>
      : view === 'learn' ? <LearningWorkspace request={request} initialSession={data.active_session} onSession={active => setData(previous => ({...previous, active_session: active}))}/> : view === 'practice' ? <PracticeWorkspace request={request} selection={selection} onUpdated={refreshProgress}/> : view === 'progress' ? <ProgressView request={request} onPractice={practice}/>
      : <Dashboard data={data} onLearn={() => setView('learn')} onPractice={practice}/>}
      <footer>Learn with intention. Practice with feedback. Return with confidence.</footer>
    </main>
  </div>;
}

function ProfileForm({ profile, onSaved }) {
  const [form, setForm] = useState(profile || { target_role: 'AI/ML Engineer', experience: 'intermediate', study_minutes: 30, timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'America/New_York' });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);
  const update = e => setForm({ ...form, [e.target.name]: e.target.name === 'study_minutes' ? Number(e.target.value) : e.target.value });
  async function submit(e) {
    e.preventDefault(); setSaving(true); setError('');
    try { await request('/profile', { method: 'PUT', body: JSON.stringify(form) }); setSaved(true); await onSaved(); }
    catch (e) { setError(e.message); } finally { setSaving(false); }
  }
  return <><div className="intro"><p className="eyebrow">{profile ? 'YOUR LEARNING PROFILE' : 'LET’S GET STARTED'}</p><h1>A learning path,<br/>built around you.</h1><p>Set your direction. We’ll use it to shape your learning and practice.</p></div><form className="card profile" onSubmit={submit}><h2>{profile ? 'Update your preferences' : 'Tell us where you want to go'}</h2><label>Target role<input name="target_role" minLength="2" maxLength="120" required value={form.target_role} onChange={update}/></label><div className="form-row"><label>Current experience<select name="experience" value={form.experience} onChange={update}><option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option></select></label><label>Daily study time<select name="study_minutes" value={form.study_minutes} onChange={update}>{[15,20,30,45,60,90,120].map(n => <option key={n} value={n}>{n} minutes</option>)}</select></label></div><label>Timezone<input name="timezone" required value={form.timezone} onChange={update}/><small>Used to display your future revision schedule.</small></label>{error && <p className="error" role="alert">{error}</p>}{saved && <p role="status">Profile saved.</p>}<button className="primary" disabled={saving}>{saving ? 'Saving…' : profile ? 'Save preferences →' : 'Create my workspace →'}</button><p className="fine">Your profile is saved locally on this computer.</p></form></>;
}

function Dashboard({ data, onLearn, onPractice }) {
  const topic = data.topics[0];
  return <><div className="intro"><p className="eyebrow">YOUR NEXT CHAPTER</p><h1>Build understanding.<br/><em>Then build confidence.</em></h1><p>Your space to learn, practice, and prepare for your next {data.profile.target_role} opportunity.</p></div><div className="stats"><div><span>DAILY COMMITMENT</span><strong>{data.profile.study_minutes}<small> min</small></strong></div><div><span>SKILLS ASSESSED</span><strong>{data.assessed_skills}<small> / {topic.skills.length}</small></strong></div><div><span>REVIEWS DUE</span><strong>{data.due_reviews.length}<small> today</small></strong></div></div><div className="section-heading"><h2>Your learning path</h2><span>START WITH THE FOUNDATIONS</span></div><section className="course card"><div className="course-art" aria-hidden="true"><svg viewBox="0 0 240 170"><path d="M30 20V145H220" fill="none" stroke="#9aafa3"/><path d="M42 130L209 38" fill="none" stroke="#245f48" strokeWidth="3"/>{[[52,115],[75,120],[100,90],[126,99],[145,64],[177,60],[198,35]].map(([x,y],i)=><circle key={i} cx={x} cy={y} r="5" fill="#b8793c"/>)}</svg></div><div><span className="tag">MACHINE LEARNING · MODULE 01</span><h2>{topic.title}</h2><p>{topic.description}</p><button className="primary" onClick={onLearn}>{data.active_session ? 'Continue learning →' : 'Start learning →'}</button></div></section><div className="two-col"><section className="card"><span className="eyebrow">REVISION QUEUE</span><h2>{data.due_reviews.length ? `${data.due_reviews.length} reviews ready` : 'Keep learning, then revisit.'}</h2><p>{data.due_reviews.length ? data.due_reviews.map(r=>r.skill).join(', ') : 'No reviews due yet. Upcoming dates appear in Your progress after practice.'}</p><button className="secondary" onClick={()=>onPractice()}>Start practice →</button></section><section className="card"><span className="eyebrow">WEAK AREAS</span><h2>{data.weak_areas.length ? 'Your next opportunities.' : 'Evidence before labels.'}</h2>{data.weak_areas.length ? data.weak_areas.map(w=><div key={w.skill+w.mode}><p><strong>{w.skill}</strong> · {w.dimension}</p><p>{w.gap}</p><button className="secondary" onClick={()=>onPractice(w.skill,w.mode)}>Revisit this skill →</button></div>) : <p>No weak areas identified. Practice will help distinguish new topics from gaps.</p>}</section></div></>;
}

createRoot(document.getElementById('root')).render(<App/>);
