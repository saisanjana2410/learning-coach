"""Evaluate synthetic answer fixtures without importing the app or touching SQLite."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from time import perf_counter

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from dotenv import load_dotenv
load_dotenv(ROOT/'backend'/'.env')
from app.curriculum import QUESTIONS
from app.assessment import EVALUATOR_PROMPT_VERSION, evaluate_answer, validate_evaluation, score

def expected_score(expected):
    if 'insufficient_evidence' in expected.values():return None
    points={'met':1,'partial':.5,'not_met':0}
    return round(100*sum(points[v] for v in expected.values())/len(expected))

def load_cases(path):
    document=json.loads(Path(path).read_text(encoding='utf-8'))
    questions={q['id']:q for q in QUESTIONS}
    ids=set()
    for case in document['cases']:
        if case['id'] in ids:raise ValueError('Duplicate fixture ID')
        ids.add(case['id'])
        q=questions[case['question_id']]
        if set(case['expected'])!=set(q['criteria']):raise ValueError('Fixture rubric mismatch')
        expected_score(case['expected'])
    return document

def evaluate_case(case,repetition,evaluator=evaluate_answer):
    q=next(q for q in QUESTIONS if q['id']==case['question_id'])
    started=perf_counter()
    result={'case_id':case['id'],'question_id':q['id'],'category':case['category'],'repetition':repetition,
            'equivalence_group':case.get('equivalence_group'),'expected':case['expected'],'expected_score':expected_score(case['expected'])}
    try:
        evaluation=validate_evaluation(evaluator(q,case['answer']),q,case['answer'])
        result.update(valid=True,judgments={c.id:c.result for c in evaluation.criteria},score=score(evaluation),feedback=evaluation.model_dump())
    except Exception as exc:
        # Avoid logging raw provider errors, which may include request data or credentials.
        result.update(valid=False,error_type=type(exc).__name__,judgments={},score=None)
    result['latency_seconds']=round(perf_counter()-started,3)
    return result

def metrics(results):
    total=len(results);criteria=sum(len(r['expected']) for r in results)
    agreement=sum(r['valid'] and r['judgments'].get(k)==v for r in results for k,v in r['expected'].items())
    pairs=[]
    for case_id in {r['case_id'] for r in results}:
        repeats=sorted([r for r in results if r['case_id']==case_id],key=lambda r:r['repetition'])
        if len(repeats)>1:pairs.append(all(r['valid'] for r in repeats) and all(r['judgments']==repeats[0]['judgments'] for r in repeats))
    equivalent=[]
    for group,repetition in {(r['equivalence_group'],r['repetition']) for r in results if r['equivalence_group']}:
        members=[r for r in results if r['equivalence_group']==group and r['repetition']==repetition]
        if len(members)>1:equivalent.append(all(r['valid'] for r in members) and all(r['judgments']==members[0]['judgments'] for r in members))
    return {'completed_calls':total,'valid_calls':sum(r['valid'] for r in results),
            'criterion_agreement':round(agreement/criteria,4) if criteria else None,'criterion_count':criteria,
            'score_agreement':round(sum(r['valid'] and r['score']==r['expected_score'] for r in results)/total,4) if total else None,
            'repeat_consistency':round(sum(pairs)/len(pairs),4) if pairs else None,'repeated_cases':len(pairs),
            'equivalent_answer_consistency':round(sum(equivalent)/len(equivalent),4) if equivalent else None,'equivalent_pairs':len(equivalent),
            'disagreement_cases':sorted({r['case_id'] for r in results if not r['valid'] or r['judgments']!=r['expected']})}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--cases',type=Path,default=ROOT/'evals'/'feedback_cases.json')
    parser.add_argument('--output',type=Path,default=ROOT/'evals'/'reports'/'feedback_baseline.json')
    parser.add_argument('--repetitions',type=int,choices=range(1,6),default=2)
    parser.add_argument('--limit',type=int,default=20)
    parser.add_argument('--workers',type=int,choices=range(1,5),default=2)
    args=parser.parse_args()
    if args.limit<1:parser.error('--limit must be positive')
    if not os.getenv('OPENAI_API_KEY'):parser.error('Configure the backend OpenAI key first')
    dataset=load_cases(args.cases);cases=dataset['cases'][:args.limit]
    report={'status':'running','started_at':datetime.now(timezone.utc).isoformat(),
        'model':os.getenv('OPENAI_MODEL','gpt-4.1-mini'),'prompt_version':EVALUATOR_PROMPT_VERSION,
        'dataset_version':dataset['version'],'dataset_sha256':hashlib.sha256(args.cases.read_bytes()).hexdigest(),
        'label_provenance':dataset['label_provenance'],'limitation':dataset['purpose'],
        'request_accounting':'Call counts represent evaluation attempts, not provider API requests; a validation correction can use one additional request.',
        'case_count':len(cases),'repetitions':args.repetitions,'requested_calls':len(cases)*args.repetitions,
        'questions':{q['id']:q for q in QUESTIONS if q['id'] in {c['question_id'] for c in cases}},'results':[]}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    def save():
        report['metrics']=metrics(report['results'])
        args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    save()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(evaluate_case,c,r) for c in cases for r in range(1,args.repetitions+1)]
        for future in as_completed(futures):
            report['results'].append(future.result());save()
            print(f"Completed {len(report['results'])}/{report['requested_calls']}",flush=True)
    report['status']='complete';report['finished_at']=datetime.now(timezone.utc).isoformat();save()
    print(json.dumps(report['metrics']),flush=True)

if __name__=='__main__':main()
