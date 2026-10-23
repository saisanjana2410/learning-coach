import React,{useEffect,useState} from 'react';

function stamp(value,timezone){return value?new Date(value).toLocaleString(undefined,{timeZone:timezone}):'Not checked yet';}

export default function TechUpdates({request,onLesson,onTopic}){
 const [data,setData]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [useAI,setUseAI]=useState(false),[view,setView]=useState('digest'),[message,setMessage]=useState('');
 async function load(){setError('');try{setData(await request('/tech-updates'));}catch(e){setError(e.message);}}
 useEffect(()=>{load();},[]);
 async function refresh(){setBusy(true);setError('');setMessage('');try{
  const value=await request('/tech-updates/refresh',{method:'POST',body:JSON.stringify({use_ai:useAI})});setData(value);
  setMessage(value.cache_reason==='recent_check'?`A check was made less than a minute ago. The saved digest is shown; refresh is available after ${stamp(value.refresh_after,value.timezone)}.`:value.cache_reused?'The qualifying source items are unchanged. The saved digest was reused without another summary request.':'Source check finished. Announcement dates are shown on each card.');
 }catch(e){setError(e.message);}finally{setBusy(false);}}
 async function save(item){setBusy(true);setError('');try{setData(await request(`/tech-updates/${item.id}/save`,{method:'PUT',body:JSON.stringify({saved:!item.saved})}));}catch(e){setError(e.message);}finally{setBusy(false);}}
 const cards=view==='saved'?(data?.saved_items||[]):(data?.digest?.items||[]);
 return <><div className="intro"><p className="eyebrow">STAY CURRENT</p><h1>Today’s relevant updates.</h1><p>A short, source-linked digest for AI/ML engineering. Learn what changed and choose what deserves your attention.</p></div>
 {error&&<p className="error" role="alert">{error} <button className="secondary" disabled={busy} onClick={load}>Reload saved digest</button></p>}
 {!data?<p role="status">Loading saved updates…</p>:<>
 <section className="card updates-controls"><h2>Check once. Read whenever.</h2>
 <p>Opening this section uses the saved digest. Refresh checks official feeds for relevant announcements from the last {data.window_days} days; it does not run automatically.</p>
 <label className="updates-ai"><input type="checkbox" checked={useAI} disabled={busy} onChange={e=>setUseAI(e.target.checked)}/> AI summaries (uses OpenAI API tokens when new summaries are needed)</label>
 <p className="fine">Unchecked: source excerpts and curated learning suggestions, with no model call. Checked: one bounded summary request for changed items, then cached. Only public update text is sent; your drafts, job description and learning history are not included.</p>
 <button className="primary" disabled={busy} onClick={refresh}>{busy?'Checking official sources…':'Refresh updates →'}</button>
 <p>Last checked: {stamp(data.last_checked_at,data.timezone)} · {data.timezone}</p>
 {data.last_successful_at&&<p className="fine">Digest saved: {stamp(data.last_successful_at,data.timezone)}</p>}
 {data.needs_refresh&&<p className="fine">A fresh source check is recommended. Existing cards retain their original announcement dates.</p>}
 {message&&<p role="status">{message}</p>}{data.notice&&<p role="status">{data.notice}</p>}{data.digest?.notice&&<p role="status">{data.digest.notice}</p>}
 </section>
 <div className="lesson-tabs updates-tabs" aria-label="Update views"><button className={view==='digest'?'active':''} onClick={()=>setView('digest')}>Recent digest ({data.digest?.items.length||0})</button><button className={view==='saved'?'active':''} onClick={()=>setView('saved')}>Saved for later ({data.saved_items.length})</button></div>
 <p className="fine">{view==='saved'?'Saved snapshots may be older than the current news window.':`Up to five relevant items, with at most one per source. This is a curated feed selection, not exhaustive news coverage. ${data.today} is today in your learning-profile timezone.`}</p>
 {cards.length===0&&<section className="card"><h2>{view==='saved'?'Your reading list is empty.':data.digest?'No qualifying updates found.':'Ready when you are.'}</h2><p>{view==='saved'?'Save an update from the digest to revisit it here.':data.digest?'There may be fewer than three meaningful announcements in the checked sources. We won’t fill the digest with unrelated items.':'Refresh to check the official sources. No update has been invented or fetched just by opening this page.'}</p></section>}
 <div className="updates-grid">{cards.map(item=><article className="card update-card" key={item.id}><div><span className="tag">{item.category}</span>{item.is_today&&<span className="pill">Source dated today</span>}</div>
 <h2><a href={item.url} target="_blank" rel="noreferrer">{item.title}</a></h2>
 <p className="fine">{item.source} · {item.date_kind==='published'?'Published':'Source updated'} <time dateTime={item.source_date} title={`Source timestamp: ${item.source_date}`}>{item.source_day}</time> {item.date_precision==='date'?'(source date)':`(${data.timezone})`}</p>
 <span className="pill">{item.summary_kind==='ai_summary'?'AI summary · check original source':'Source excerpt'}</span><p>{item.summary}</p>
 <h3>Why it may matter</h3><p>{item.why_it_matters}</p><h3>Suggested learning action</h3><p>{item.learning_action}</p>
 {item.related?.lesson_id?<button className="secondary" disabled={busy} onClick={()=>onLesson({submoduleId:item.related.topic_id,moduleId:item.related.module_id,level:item.related.level,lessonId:item.related.lesson_id})}>Review related foundations →</button>:item.related?.topic_id&&<button className="secondary" disabled={busy} onClick={()=>onTopic(item.related.topic_id)}>Explore related topic · coming soon</button>}
 <button className="secondary" disabled={busy} onClick={()=>save(item)} aria-pressed={item.saved}>{item.saved?'Remove from saved':'Save for later'}</button>
 {item.evidence&&<details><summary>Supporting source excerpt</summary><blockquote>{item.evidence}</blockquote></details>}
 </article>)}</div>
 <details className="card history"><summary>Official sources and last-check coverage</summary><p>Sources can fail independently. Unavailable feeds are reported; an unsuccessful full check keeps the previous digest.</p>{data.sources.map(source=><p key={source.id}><a href={source.feed_url} target="_blank" rel="noreferrer">{source.name}</a> · {source.status.replaceAll('_',' ')}{source.recent_entries!==undefined?` · ${source.recent_entries} recent entries`:''}</p>)}</details>
 </>}
 </>;
}
