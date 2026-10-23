"""A versioned catalog and small, level-specific content packs.

Role suggestions are curated defaults, not job-description extraction.
"""
from .content import LESSONS
from .questions import QUESTIONS

LEVELS=('beginner','foundational','intermediate','advanced')
MODULES=[
 {'id':'python','title':'Python for AI and ML','reason':'Write reliable data transformations, experiments, and model services.','prerequisites':[],
  'submodules':[('python-functions','Functions and reusable code',True),('python-collections','Collections and iteration',True),('python-basics','Variables and control flow',False),('numpy','NumPy arrays',False),('pandas','pandas and tabular data',False),('python-oop','Classes and project structure',False)]},
 {'id':'ml','title':'Machine learning','reason':'Train, evaluate, and reason about predictive models.','prerequisites':['python','math'],
  'submodules':[('linear-regression','Linear regression',True),('model-evaluation','Model evaluation',True),('classification','Classification algorithms',False),('clustering','Unsupervised learning and clustering',False),('feature-engineering','Preprocessing and features',False),('ensembles','Trees and ensembles',False)]},
 {'id':'math','title':'Math and statistics','reason':'Understand uncertainty, model assumptions, and optimization.','prerequisites':[],
  'submodules':[('probability','Probability and distributions',False),('linear-algebra','Linear algebra',False),('optimization','Optimization',False)]},
 {'id':'deep-learning','title':'Deep learning','reason':'Understand and train neural models after learning ML fundamentals.','prerequisites':['ml','math'],
  'submodules':[('neural-networks','Neural networks',False),('training','Training and regularization',False)]},
 {'id':'ai','title':'AI and LLM applications','reason':'Build retrieval, generation, and agent workflows and evaluate their behavior.','prerequisites':['python','ml'],
  'submodules':[('embeddings','Embeddings and retrieval',False),('agents','Tool-using agents',False),('llm-evaluation','LLM evaluation',False)]},
 {'id':'engineering','title':'ML engineering','reason':'Deliver reproducible models and maintain them after deployment.','prerequisites':['python','ml'],
  'submodules':[('apis','Model APIs and tests',False),('deployment','Deployment and monitoring',False)]},
]
SUBMODULES={sid:{'id':sid,'title':title,'module_id':m['id'],'available':available} for m in MODULES for sid,title,available in m['submodules']}

# Each pack has a real lesson, example, check, and server-side grading rubric.
# Keep this starter set intentionally small; catalog entries without packs are planned.
PACKS=[
 ('python-functions','beginner','Return values','Functions turn inputs into outputs',
  'Define a function with def, give inputs names called parameters, and use return to hand a result back to the caller. A function that reaches its end without returning a value returns None.',
  'def double(x):\n    return x * 2\n\nresult = double(4)  # result is 8\n\nprint displays a value; return makes it available to another expression.',
  'For def double(x): return x * 2, what is double(4)? Explain how return differs from print.',
  ['output','return_value'],'double(4) returns 8. return supplies a value to the caller; print writes to output and its own return value is None.'),
 ('python-functions','intermediate','Safe function defaults','Avoid shared mutable defaults',
  'Python evaluates a default argument once when a function is defined. If the default is a mutable list, later calls reuse it. Use None when each call needs a fresh list.',
  'def collect(value, items=None):\n    if items is None:\n        items = []\n    items.append(value)\n    return items\n\nCall collect(1) and collect(2) independently: they return [1] and [2].',
  'Why can def collect(x, items=[]): items.append(x); return items retain values between calls? Explain a safe replacement.',
  ['evaluation_time','replacement'],'The list default is evaluated once at definition time and shared across calls. Use items=None and initialize a new list inside the function if items is None.'),
 ('python-functions','advanced','Closure binding','Reason about closures and binding',
  'A closure retains access to variables from an enclosing scope. A lambda in a loop normally looks up the captured loop variable when called, rather than freezing its value at creation time.',
  'functions = [lambda: i for i in range(3)]\n# Calling each after the loop yields 2, 2, 2.\n\nfunctions = [lambda i=i: i for i in range(3)]\n# Defaults bind at definition: calls yield 0, 1, 2.',
  'Why do [lambda: i for i in range(3)] produce functions returning 2 after the loop? Show how to capture each iteration value.',
  ['late_binding','capture'],'The closures share a binding looked up at call time, whose final loop value is 2. Use lambda i=i: i to bind each current value as a default argument, or use a factory function.'),
 ('python-collections','beginner','Collection lookup','Choose lists and dictionaries',
  'A list holds an ordered sequence accessed by zero-based positions. A dictionary associates keys with values. Choose a dictionary when labels, rather than positions, identify your data.',
  "scores = [70, 85, 90]\nfirst = scores[0]  # 70\nlearner = {'name': 'Ari', 'score': 85}\nscore = learner['score']  # 85",
  "Given scores=[70,85,90] and learner={'score':85}, what do scores[0] and learner['score'] return? Why choose a dictionary for named fields?",
  ['lookup','structure'],'scores[0] is 70 and learner[\'score\'] is 85. A dictionary retrieves values by meaningful keys and is appropriate for named fields; a list uses positional indices.'),
 ('python-collections','intermediate','Comprehensions','Transform data without mutating inputs',
  'A comprehension expresses a transformation and optional filter. It builds a new collection. A copy of an outer collection can still share nested mutable objects, so be deliberate about mutation.',
  'values = [1, 2, 3, 4]\nsquares = [x * x for x in values if x % 2 == 0]\n# squares is [4, 16]; values remains unchanged.',
  'Write a list comprehension for the squares of even numbers in [1,2,3,4]. State the result and whether the original list changes.',
  ['transformation','mutation'],'[x*x for x in [1,2,3,4] if x % 2 == 0] produces [4,16]. It creates a new list without modifying the original.'),
 ('python-collections','advanced','Lazy iteration','Process data with generators',
  'A generator produces values on demand instead of storing the entire output. It can reduce memory use when processing a large input stream, but it is consumed as you iterate and is not a reusable materialized collection.',
  'squares = (x*x for x in range(1000000))\nfirst = next(squares)  # 0\nsecond = next(squares) # 1\n\nA list comprehension materializes all results; this generator does not.',
  'Compare a generator expression with a list comprehension for a million transformed records. Explain memory behavior and what happens when you iterate the same generator again after exhaustion.',
  ['memory','exhaustion'],'A generator yields values lazily and avoids materializing the entire output; a list stores all output elements. A consumed generator is exhausted and must be recreated to iterate again.'),
 ('linear-regression','intermediate','Regression pipelines','Evaluate preprocessing with the model',
  'Preprocessing is part of the learned model procedure. Split data first and fit preprocessing only on training observations. A pipeline keeps the scaler and model together so cross-validation refits both within each training fold.',
  'Pipeline([("scale", StandardScaler()), ("model", Ridge())])\n\nCross-validate the entire pipeline rather than scaling all observations first. This preserves the boundary between each training fold and its validation fold.',
  'Why should scaling and regression be cross-validated as one pipeline instead of scaling the full dataset before cross-validation?',
  ['leakage','fold_fitting'],'Scaling the full dataset leaks held-out distribution information into training. Cross-validating a pipeline fits the scaler and estimator only within each training fold, then transforms its validation fold.'),
 ('linear-regression','advanced','Regularization tradeoffs','Handle correlated regression features',
  'Highly correlated predictors can make ordinary least-squares coefficients sensitive to small data changes. Ridge adds an L2 coefficient penalty, shrinking coefficients and often reducing variance at the cost of bias. Scaling affects the penalty across features.',
  'If two features nearly duplicate each other, their individual coefficients may change substantially while predictions remain similar. Compare validation performance and coefficient stability across penalty strengths; do not choose the strength using the final test set.',
  'Why can correlated predictors make OLS coefficients unstable? Explain how ridge helps and why scaling and held-out tuning matter.',
  ['instability','regularization','validation'],'Collinear predictors make individual coefficient estimates poorly determined and sensitive to noise. Ridge adds an L2 penalty that shrinks coefficients and can reduce variance, introducing bias. Scale within training folds so the penalty is comparable across feature units, and tune its strength with validation rather than the final test set.'),
 ('model-evaluation','beginner','Baseline accuracy','Look beyond accuracy',
  'Accuracy is the fraction of all predictions that are correct. It can conceal poor detection of a rare class. Compare with a simple baseline, inspect a confusion matrix, and examine positive-class precision and recall.',
  'With 100 cases and only one positive, predicting negative every time is 99% accurate but finds no positives. Recall for the positive class is zero.',
  'Only 1% of cases are positive. An always-negative classifier gets 99% accuracy. Is this necessarily useful? Name metrics that reveal its weakness.',
  ['baseline','recall'],'It may be useless for finding positives despite 99% accuracy. Positive recall is zero. Inspect recall, precision with its zero-denominator convention, the confusion matrix, and precision-recall metrics appropriate to the task.'),
 ('model-evaluation','intermediate','Validation design','Separate tuning from final evaluation',
  'Use training data to fit parameters, validation data to choose configurations, and an untouched test set to estimate the final procedure. Repeatedly selecting models based on test scores makes that test set part of development.',
  'Compare model settings using cross-validation on the development data. Choose a setting, refit on the permitted development data, and evaluate once on the held-out test data. Respect groups and time when choosing splits.',
  'You choose between many models using their test-set scores and report the best score. What is the problem, and how should the evaluation be organized?',
  ['selection_bias','split_roles'],'Repeated selection on the test set biases its reported performance upward. Use validation or cross-validation for model selection and keep an independent final test set untouched until the procedure is chosen.'),
 ('model-evaluation','advanced','Temporal evaluation','Evaluate under time and group dependence',
  'Random splits can mix future and past observations or related entities across training and validation. A useful evaluation should reflect the deployment boundary: time-ordered splits for forecasting and group-aware splits for unseen entities.',
  'When predicting next month outcomes from historical features, train on earlier periods and evaluate on later ones. If features aggregate over future windows, audit their availability timestamps and consider a gap between training and validation.',
  'Why can random cross-validation overestimate a time-dependent model? Propose a split strategy and a feature-availability check.',
  ['dependence','deployment_split','availability'],'Random folds can leak future information or correlated temporal observations. Use rolling or forward time splits with training before validation, and gaps when windows overlap. Verify every feature was available at prediction time rather than using future outcomes.'),
]

for submodule,level,skill,title,concept,example,prompt,criteria,reference in PACKS:
    sid=f'{submodule}-{level}'
    metadata={'module_id':SUBMODULES[submodule]['module_id'],'submodule_id':submodule,'level':level}
    LESSONS.append({'id':sid,'version':1,'title':title,'skill':skill,'minutes':8,**metadata,
        'sections':[{'heading':'Understand the idea','text':concept},{'heading':'Work through an example','text':example},{'heading':'Check your understanding','text':prompt}],
        'takeaway':concept.split('. ')[0]+'.'})
    QUESTIONS.append({'id':sid+'-check','version':1,'skill':skill,'lesson_id':sid,'topic_id':submodule,**metadata,
        'prompt':prompt,'hint':concept,'criteria':criteria,'reference':reference})

ALTERNATES={
 'Return values':('A function add(a,b) prints a+b but has no return statement. What is stored by result=add(2,3)? How would you change the function so result stores 5?',
                  'It displays 5 but result is None, because the function has no return statement. Use return a+b so the caller receives 5 instead of only printing it.'),
 'Safe function defaults':('A function stores results in a default dictionary cache={}. Why might separate callers unexpectedly share results? Show how to give each call its own dictionary when none is provided.',
                         'The default dictionary is created once at function definition, so mutations persist between calls. Use cache=None and assign cache={} inside the function if cache is None.'),
 'Closure binding':('You build callbacks with callbacks=[lambda: name for name in ["Ada","Lin"]]. After the comprehension, what does each callback return, and how can each retain its own name?',
                    'Both return Lin because they look up the same enclosing name binding at call time after its final assignment. Use lambda name=name: name or a factory function to capture the value for each callback.'),
 'Collection lookup':('Given rows=[{"label":"cat"},{"label":"dog"}], what is rows[1]["label"]? Explain which operation uses an index and which uses a key.',
                       'It returns dog. rows[1] selects the second list element by a zero-based index; ["label"] retrieves that dictionary value by its key.'),
 'Comprehensions':('For values=[-2,0,3], write a comprehension that doubles only positive values. State the output and whether values changes.',
                     '[x*2 for x in values if x>0] produces [6] and leaves the original list [-2,0,3] unchanged.'),
 'Lazy iteration':('A developer calls sum(g) twice where g=(x for x in range(1000000)). Why is the second sum zero, and how does this approach compare in memory use with storing a list?',
                    'The first sum consumes the generator, so the second sees no values and returns zero. Lazy generation avoids storing a million-item output list. Recreate the generator to repeat the calculation.'),
 'Regression pipelines':('You impute missing values using the mean of all rows before cross-validating a regression model. Explain the leakage and how to organize imputation during cross-validation.',
                          'Validation observations influenced the imputation mean. Place the imputer and regressor in one pipeline; fit the imputer within each training fold and apply its fitted transformation to that fold validation data.'),
 'Regularization tradeoffs':('Two predictors are almost duplicates and OLS coefficients vary dramatically across samples. Explain why, how an L2 penalty changes the tradeoff, and how you would choose the penalty without leakage.',
                             'Collinearity makes separate OLS coefficients poorly determined and sensitive to noise. Ridge shrinks coefficients with an L2 penalty, adding bias while often reducing variance. Scale within training folds and select the strength through validation, keeping the final test set untouched.'),
 'Baseline accuracy':('Of 100 examples, 5 are positive. A classifier always predicts negative. Calculate accuracy and positive recall, and explain why accuracy alone is inadequate.',
                      'Accuracy is 95% but positive recall is zero because none of the 5 positives is detected. Inspect the confusion matrix, recall and precision or suitable precision-recall metrics rather than relying on accuracy alone.'),
 'Validation design':('After seeing a final test score, you repeatedly adjust hyperparameters until that score improves. Can you treat the same score as an independent final estimate? Propose a better workflow.',
                       'No. Repeated test-driven tuning creates selection bias and makes the test part of development. Tune using validation or cross-validation on development data, then evaluate the chosen procedure on an independent untouched test set.'),
 'Temporal evaluation':('A demand model uses a feature computed from next-week sales and is validated with random folds of daily records. Identify two problems and propose an evaluation reflecting future deployment.',
                         'Future sales are unavailable at prediction time and random folds mix future and past observations. Remove or time-shift features to use only then-available data, and use forward time splits, with a gap if windows overlap.'),
}
for q in list(QUESTIONS):
    if q['skill'] in ALTERNATES and q['id'].endswith('-check'):
        prompt,reference=ALTERNATES[q['skill']]
        QUESTIONS.append({**q,'id':q['id']+'-transfer','prompt':prompt,'reference':reference})

# Existing records keep their IDs. Only the live content catalog receives metadata.
for lesson in LESSONS:
    lesson.setdefault('module_id','ml');lesson.setdefault('submodule_id','linear-regression');lesson.setdefault('level','beginner')
for q in QUESTIONS:
    if 'module_id' in q:continue
    topic=q.get('topic_id','linear-regression')
    module='python' if topic=='python' else 'sql' if topic=='sql' else 'ml'
    submodule=('python-functions' if q['id']=='python-mutable' else 'python-collections') if module=='python' else 'model-evaluation' if topic=='ml-foundations' else topic
    q.update(module_id=module,submodule_id=submodule,level='intermediate' if module in ('python','sql') else 'beginner',topic_id=submodule)
    if module=='python':q['lesson_id']=submodule+'-intermediate'
    elif submodule=='model-evaluation':q['lesson_id']='model-evaluation-beginner'
    elif module=='sql':q['lesson_id']=None

CRITERION_DESCRIPTIONS={
 'python-functions-beginner-check':{
     'output':'Correctly gives the returned numeric result for the specified function call. A concise correct value is sufficient; no derivation or terminology is required.',
     'return_value':'Distinguishes returning a usable value to the caller from displaying output using print.'},
 'python-functions-intermediate-check':{
     'evaluation_time':'Explains that the mutable default is evaluated once at function definition and reused by later calls.',
     'replacement':'Proposes a None default with a new list initialized inside the function when no list was provided.'},
 'residual-positive':{
     'calculation':'Computes actual minus predicted correctly with the signed result and appropriate units.',
     'interpretation':'Explicitly explains that the prediction is too low or that the model underpredicted. A numeric residual alone does not answer the interpretation request.'},
 'model-evaluation-intermediate-check':{
     'selection_bias':'Explains that selecting on test scores makes the winning estimate optimistic or no longer independent. The technical phrase selection bias is not required.',
     'split_roles':'Uses validation or cross-validation for model selection and reserves independent final test data for evaluation.'},
}
for q in QUESTIONS:
    if q['id'] in CRITERION_DESCRIPTIONS:
        q['criterion_descriptions']=CRITERION_DESCRIPTIONS[q['id']]
        q['version']=2

def module_for_skill(skill):
    return next((q for q in QUESTIONS if q['skill']==skill),None)

def question_metadata(question):
    # Legacy records lack catalog metadata; new snapshots retain their own identity.
    current=next((q for q in QUESTIONS if q['id']==question['id']),{})
    return {**current,**question}

from .track_catalog import build_track_catalog, resolve_role
TRACK_CATALOG=build_track_catalog(MODULES,SUBMODULES)
from .python_basics import install as install_python_basics
install_python_basics(MODULES,SUBMODULES,LESSONS,QUESTIONS)
from .focused_ml import install as install_focused_ml
install_focused_ml(MODULES,SUBMODULES,LESSONS,QUESTIONS,TRACK_CATALOG)

def role_path(role):
    role_id=resolve_role(role)
    track=next((r for r in TRACK_CATALOG['roles'] if r['id']==role_id),None)
    if track:
        ids=[SUBMODULES[link['topic_id']]['module_id'] for link in TRACK_CATALOG['role_topics'] if link['role_id']==role_id]
        return list(dict.fromkeys(ids)),track['title']+' learning path'
    return ['python','math','ml'], 'General technical starting path; tailor it to your target role'

def scoped_questions(topic_id,level,module_levels=None,topic_levels=None):
    return [q for q in QUESTIONS if (q['submodule_id']==topic_id if topic_id else True)
            and q['level']==((topic_levels or {}).get(q['submodule_id'],module_levels.get(q['module_id'],level)) if module_levels is not None else level)]
