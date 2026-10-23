"""Authored Python variables/types lessons; examples run locally, never on the server."""
VERSION='python-basics-lessons-v2'
READING=[
    {'title':'Python tutorial: numbers and text','url':'https://docs.python.org/3/tutorial/introduction.html'},
    {'title':'Python built-in types','url':'https://docs.python.org/3/library/stdtypes.html'},
]

PACKS=[
    {
      'level':'beginner','title':'Names, values and everyday types','skill':'Python names and types',
      'objective':'Create named values, identify int/float/str/bool/None and calculate a useful result.',
      'prerequisites':'No Python knowledge required. Open a Python 3 interpreter or save a file and run it with python filename.py.',
      'why':'A learning tracker needs a topic name, a session count and a target. Choosing suitable types makes its calculations understandable.',
      'concept':'Assignment with = binds a name to a value. int represents whole numbers; float represents approximate real numbers; str represents text; bool represents True or False; None represents absence. Reassigning one name does not change another name bound to an immutable number. Use == to compare values. Names are case-sensitive. Quotes turn digits into text: "3" is not the number 3.',
      'example':'sessions = 3 binds sessions to an integer. minutes = sessions * 20 computes 60. topic = "Python" is text. completed = minutes >= 60 is True. print displays a result; it does not store that result for you.',
      'code':'topic = "Python"\nsessions = 3\nminutes_per_session = 20\nminutes = sessions * minutes_per_session\ncompleted = minutes >= 60\nnote = None\nprint(topic, minutes, completed, note)\nprint(type(sessions).__name__, type(completed).__name__)\n',
      'output':'Python 60 True None\nint bool\n',
      'guided':'Change sessions to 2. Predict minutes and completed before running the sample. Expected: 40 and False. Change the topic string without changing the calculation.',
      'challenge':'Create target_minutes = 90 and studied_minutes = 35. Compute remaining_minutes, create reached_target using >=, and print both. Expected: 55 and False. Explain why "35" would be a poor choice for arithmetic.',
      'project':'Build a study-session receipt using topic = "Python", sessions = 4 and minutes_per_session = 15. Submit code that calculates total_minutes and reached_target for a 60-minute target, plus its expected output. Explain the types of total_minutes and reached_target.',
      'rubric':{'calculation':'Computes total_minutes as sessions * minutes_per_session, yielding 60.',
                'boolean':'Computes reached_target by comparing total_minutes with 60, yielding True.',
                'types':'Explains that total_minutes is int and reached_target is bool.'},
      'reference':'topic = "Python"\nsessions = 4\nminutes_per_session = 15\ntotal_minutes = sessions * minutes_per_session\nreached_target = total_minutes >= 60\nprint(total_minutes, reached_target)\n# 60 True; total_minutes is int, reached_target is bool.',
      'quiz':'Given a = 5; b = a; a = 8, what are a and b? Explain why b stays unchanged. What is the type and value of a > b?',
      'quiz_rubric':{'binding':'States a is 8 and b is 5; reassigning a does not reassign b.', 'comparison':'States a > b is True and has type bool.'},
      'quiz_reference':'a is 8 and b remains 5: assignment rebinds a rather than changing the integer bound to b. a > b is True, a bool.',
      'next':['python-control-flow','python-functions'],
    },
    {
      'level':'foundational','title':'Convert input and preserve missing values','skill':'Python input conversion',
      'objective':'Convert trusted numeric text, distinguish zero from missing data and explain conversion errors.',
      'prerequisites':'Know assignment, basic types and arithmetic. The example uses a small if statement: its indented body runs when the condition is True.',
      'why':'Forms and environment variables supply text. A tracker must convert numeric input while preserving a valid zero rather than replacing it with a default.',
      'concept':'input() returns str. int("20") converts valid integer text; int("twenty") raises ValueError. int("2.5") also raises ValueError. Do not use bool("False") to parse a flag: any nonempty string is truthy. None can mean missing; 0 can mean a valid measured value. Test value is None when only absence should trigger a default. This lesson handles trusted integer text; validating arbitrary external input needs explicit error handling.',
      'example':'If supplied_minutes is 0, supplied_minutes or 25 yields 25 because zero is falsey. Checking is None instead retains 0. Calling int on stripped " 20 " yields 20, so two sessions total 40 minutes.',
      'code':'raw_minutes = " 20 "\nminutes = int(raw_minutes.strip())\nsessions = 2\nsupplied_break = 0\nif supplied_break is None:\n    supplied_break = 5\nprint(minutes * sessions, supplied_break)\nprint(bool("False"))\n',
      'output':'40 0\nTrue\n',
      'guided':'Set supplied_break to None and predict the output: 40 5, then True. Restore it to 0 and explain why the break remains zero. Replace raw_minutes with "twenty" and identify ValueError; do not silently turn bad text into zero.',
      'challenge':'Convert raw_sessions = "3" and raw_minutes = "15" to integers and compute 45. Explain why raw_sessions + raw_minutes produces "315". State what int("3.5") does and why bool("False") is unsuitable for parsing a boolean flag.',
      'project':'Write code for a tracker with raw_sessions = "3", raw_minutes = "15" and supplied_break = 0. Convert the strings and calculate total study minutes. Use a default break of 5 only if supplied_break is None. Print the total and break, explain the output, and state what should happen for invalid integer text instead of silently inventing a measurement.',
      'rubric':{'conversion':'Explicitly converts both numeric strings to int and calculates 45.',
                'missing':'Uses an explicit None check to retain the valid zero break.',
                'failure':'Identifies ValueError for invalid integer text and rejects/reports bad input rather than inventing zero.'},
      'reference':'sessions = int("3")\nminutes = int("15")\nsupplied_break = 0\nif supplied_break is None:\n    supplied_break = 5\nprint(sessions * minutes, supplied_break)\n# 45 0. Invalid integer text raises ValueError; report it to the caller/user rather than treating it as measured zero.',
      'quiz':'Predict "3" + "15", int("3") + int("15"), and bool("False"). Explain the difference between a missing value None and a valid measured value 0.',
      'quiz_rubric':{'conversion':'Gives "315" for concatenation and 18 for integer addition.', 'truth':'Gives True for the nonempty string "False".', 'missing':'Distinguishes absent None from valid zero; recommends is None for an absence-only default.'},
      'quiz_reference':'The results are "315", 18 and True. Text + concatenates; int conversion enables numeric addition. Nonempty strings are truthy. None indicates missing; 0 may be a valid measurement, so use is None for an absence-only fallback.',
      'next':['python-control-flow','python-exceptions'],
    },
    {
      'level':'intermediate','title':'Types at an application boundary','skill':'Python runtime type boundaries',
      'objective':'Separate runtime validation from type hints and distinguish bool from integer measurements.',
      'prerequisites':'Comfortable with basic conversions, functions, if statements and raising exceptions. Review Functions and reusable code first if needed.',
      'why':'A tracker receiving JSON should not accept true as one minute or silently truncate 2.5 minutes. The boundary needs a precise data contract.',
      'concept':'Type annotations document intent and support external checkers; Python does not enforce them automatically at runtime. bool is a subclass of int, so isinstance(True, int) is True. When a contract requires exactly a built-in integer, type(value) is int rejects booleans and subclasses deliberately. Validation policy depends on the application: exact-type checks are not a universal replacement for polymorphism. Preserve None separately when it means absence.',
      'example':'For a strict whole-minute field, validate exact int and nonnegative value before doing arithmetic. int(2.5) would truncate toward zero; int(True) yields 1. Both conversions would mask a contract violation if these inputs are forbidden.',
      'code':'def validate_minutes(value: int) -> int:\n    if type(value) is not int:\n        raise TypeError("minutes must be a built-in int")\n    if value < 0:\n        raise ValueError("minutes must be nonnegative")\n    return value\n\nprint(validate_minutes(0), validate_minutes(25))\nprint(isinstance(True, int), type(True) is int)\n',
      'output':'0 25\nTrue False\n',
      'guided':'Call validate_minutes(True), validate_minutes(2.5), then validate_minutes(-1) separately. Predict TypeError, TypeError and ValueError. Explain why the annotation alone cannot reject these calls.',
      'challenge':'Describe a validation policy that permits None as missing, retains 0, rejects True and rejects negative integers. Show the order of checks. Explain whether you intend to accept integer subclasses and why.',
      'project':'Implement validate_minutes(value) for a JSON-like input: None means missing and must be returned unchanged; a nonnegative built-in int is accepted; bool, str and float raise TypeError; negative int raises ValueError. Submit code and expected outcomes for None, 0, 25, True, "25", 2.5 and -1. Explain why annotations and isinstance(value, int) alone do not enforce this contract.',
      'rubric':{'missing':'Returns None unchanged before numeric validation, and accepts 0 and 25.',
                'strict_type':'Rejects bool, str and float with TypeError, using an exact built-in int check or an equivalent explicit policy.',
                'range':'Raises ValueError for negative integers.',
                'reasoning':'Explains annotations are not runtime enforcement and bool passes isinstance(value, int).'},
      'reference':'def validate_minutes(value):\n    if value is None:\n        return None\n    if type(value) is not int:\n        raise TypeError("expected built-in int")\n    if value < 0:\n        raise ValueError("negative minutes")\n    return value\n# None -> None; 0 -> 0; 25 -> 25; True, "25", 2.5 -> TypeError; -1 -> ValueError. Type hints alone do not validate calls; bool is an int subclass.',
      'quiz':'A function annotated minutes: int accepts True when it checks isinstance(minutes, int). Why? Explain whether the annotation prevents calling it with "25", and propose a strict built-in integer check that preserves 0.',
      'quiz_rubric':{'bool_subclass':'Explains bool subclasses int, so isinstance(True, int) is True.', 'annotation':'States annotations do not automatically enforce runtime argument types.', 'validation':'Uses type(minutes) is int or an equivalent bool-excluding check, without rejecting valid zero by truthiness.'},
      'quiz_reference':'bool subclasses int, so isinstance(True, int) is True. An int annotation does not enforce runtime checks. For a strict built-in int contract use type(minutes) is int, then separately validate range; zero remains valid.',
      'next':['python-functions','python-exceptions'],
    },
    {
      'level':'advanced','title':'Choose numeric representations deliberately','skill':'Python numeric representation',
      'objective':'Choose between int, float and Decimal at a boundary and make rounding policy explicit.',
      'prerequisites':'Know functions, imports, exceptions and basic input validation.',
      'why':'Usage counters and billing prototypes need a defined precision and rounding policy. An accidental conversion through binary float can lose the original decimal meaning.',
      'concept':'int is suitable for exact discrete counts. float uses binary floating point and cannot represent many decimal fractions exactly; approximate numerical work often uses float with suitable tolerances. Decimal constructed from decimal text preserves that decimal input; Decimal constructed from a float imports the float approximation. Decimal arithmetic still has finite context precision, and a production contract must bound input sizes, precision and rounding. Quantize makes a chosen decimal scale and rounding rule explicit. Never assume one rounding policy is correct for every application.',
      'example':'For this bounded toy contract, a unit price "0.105" and quantity 3 give Decimal("0.315"). Rounding the total once to two decimal places with ROUND_HALF_UP gives 0.32. Rounding each unit first would give 0.33; therefore where rounding happens is part of the contract.',
      'code':'from decimal import Decimal, ROUND_HALF_UP\n\nprice_text = "0.105"\nquantity = 3\ntotal = Decimal(price_text) * quantity\nrounded = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)\nprint(total, rounded)\nprint(0.1 + 0.2 == 0.3)\n',
      'output':'0.315 0.32\nFalse\n',
      'guided':'Change quantity to 2: total is 0.210 and rounded is 0.21. Compare Decimal("0.1") with Decimal(0.1). Explain why converting text to float first defeats preservation of the original decimal input.',
      'challenge':'Compare integer minor units, Decimal and float for exact whole-cent counters, fractional unit prices and approximate model features. State what validation and rounding policy each boundary needs; do not claim Decimal has unlimited arithmetic precision.',
      'project':'For a bounded prototype, calculate a line total from price_text = "0.105" and quantity = 3. Construct Decimal directly from text, multiply before rounding, and quantize once to two places with ROUND_HALF_UP. Provide code and expected output. Explain why Decimal(float(price_text)) and rounding each unit first differ from the contract. State that a real API must reject non-finite/invalid prices and invalid quantities, and specify size/precision bounds.',
      'rubric':{'representation':'Constructs Decimal directly from price_text without an intermediate float.',
                'rounding':'Multiplies by 3 before quantizing once to Decimal("0.01") with ROUND_HALF_UP, giving 0.32.',
                'tradeoff':'Explains binary float conversion imports an approximation, and rounding units first can yield 0.33.',
                'boundary':'Calls out invalid/non-finite prices, invalid quantities and explicit size/precision limits for a real API.'},
      'reference':'from decimal import Decimal, ROUND_HALF_UP\nprice_text = "0.105"\nquantity = 3\ntotal = Decimal(price_text) * quantity\nprint(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))\n# 0.32. Converting through float imports a binary approximation. Rounding each unit to 0.11 before multiplying gives 0.33. A real boundary must validate finite decimal input, allowed quantity types/ranges and size/precision bounds.',
      'quiz':'Why is 0.1 + 0.2 == 0.3 False in Python? For decimal text "0.105", compare Decimal(text) with Decimal(float(text)), and explain why rounding after summing can differ from rounding each item first.',
      'quiz_rubric':{'binary':'Explains finite binary floating-point representation approximates these decimal fractions.', 'decimal_input':'Distinguishes exact construction from decimal text from importing a float approximation.', 'rounding_order':'Explains intermediate rounding can change a total, ideally using 3 x 0.105: total-rounded 0.32 versus unit-rounded 0.33 under HALF_UP.'},
      'quiz_reference':'Binary floating point approximates these decimal fractions, so the sum is not exactly the same float as 0.3. Decimal(text) preserves the decimal input; Decimal(float(text)) imports the float approximation. With HALF_UP to cents, rounding 3 x 0.105 once gives 0.32, whereas rounding each unit to 0.11 first gives 0.33.',
      'next':['python-functions','apis'],
    },
]

TRANSFER={
 'beginner':(
    'Given x = 2; y = x; x = x + 3, give x, y and the value and type of x == y. Explain the assignments.',
    {'binding':'Gives x = 5, y = 2 and explains rebinding x leaves y unchanged.', 'comparison':'Gives False with type bool for x == y.'},
    'x is 5 and y remains 2. Rebinding x does not rebind y. x == y is False, a bool.',
    {'calculation':'Computes remaining_minutes as 90 - 35 = 55.', 'boolean':'Computes studied_minutes >= target_minutes as False.', 'types':'Explains numeric text is str and must be converted before numeric subtraction.'},
    'target_minutes = 90\nstudied_minutes = 35\nremaining_minutes = target_minutes - studied_minutes\nreached_target = studied_minutes >= target_minutes\nprint(remaining_minutes, reached_target)\n# 55 False. "35" is text, so convert it before numeric subtraction.'),
 'foundational':(
    'Predict int("4") * 2 and "4" * 2. If a valid duration is 0, why does duration or 30 lose information? Give an absence-only fallback.',
    {'conversion':'Gives 8 for integer multiplication and "44" for text repetition.', 'missing':'Explains zero is falsey and uses an is None check to preserve zero while defaulting missing values.'},
    'int("4") * 2 is 8; "4" * 2 is "44". Zero is falsey, so duration or 30 returns 30 for zero. Use 30 if duration is None else duration.',
    {'conversion':'Converts "3" and "15" to integers and calculates 45.', 'text':'Explains adding the original strings concatenates to "315".', 'errors':'Identifies ValueError for int("3.5") and True for bool("False") because it is nonempty text.'},
    'sessions = int("3")\nminutes = int("15")\nprint(sessions * minutes)\n# 45. "3" + "15" is "315". int("3.5") raises ValueError; bool("False") is True because the string is nonempty.'),
 'intermediate':(
    'A counter uses int(value) to validate whole-number input. What happens for True and 2.9? Propose a policy accepting only nonnegative built-in int values, including zero.',
    {'coercion':'Gives 1 for int(True) and 2 for int(2.9), explaining these conversions conceal invalid inputs.', 'validation':'Checks type(value) is int before testing value >= 0, retaining zero and rejecting bool/float.'},
    'int(True) is 1 and int(2.9) is 2. To reject those inputs, first require type(value) is int, then require value >= 0. Do not coerce before validation or reject zero by truthiness.',
    {'missing':'Handles None separately and preserves valid 0.', 'validation':'Rejects bool and negative integers using explicit type/range checks.', 'policy':'Explicitly states whether integer subclasses are allowed and explains that decision.'},
    'if value is None: return None; then require type(value) is int and value >= 0. This retains 0, rejects True and negative values. An exact built-in int contract deliberately excludes subclasses; an alternative contract may permit subclasses while explicitly rejecting bool.'),
 'advanced':(
    'A prototype rounds a Decimal unit price "0.045" to cents with ROUND_HALF_UP before multiplying by 3. Compare this with multiplying first and rounding the total once. Which matches a round-once-at-total contract?',
    {'results':'Gives 0.15 for unit-first rounding and 0.14 for rounding the 0.135 total.', 'policy':'Chooses multiply then quantize once and explains rounding stage is part of the contract.'},
    'Unit-first gives 0.05 * 3 = 0.15. Multiplying first gives 0.135, which HALF_UP quantizes to 0.14. The latter matches the specified round-once-at-total contract.',
    {'counts':'Chooses integer minor units for exact whole-cent counts, while noting fractional unit prices need an explicit representation and rounding policy.', 'decimal':'Uses Decimal from text for decimal prices and specifies finite context precision and rounding.', 'float':'Uses float for approximate model features with appropriate tolerances and input validation.'},
    'Use int minor units for whole-cent counts. For fractional decimal prices use Decimal from validated text, bounded precision and explicit rounding stage/mode. For approximate model features float is often suitable with finite/range validation and appropriate tolerances. Decimal arithmetic still has finite context precision.'),
}


def install(modules,submodules,lessons,questions):
    topic=submodules['python-basics']
    topic.update(title='Variables and data types',available=True)
    module=next(m for m in modules if m['id']=='python')
    module['submodules']=[(sid,topic['title'],True) if sid=='python-basics' else (sid,title,available)
                          for sid,title,available in module['submodules']]
    for pack in PACKS:
        lesson_id='python-basics-'+pack['level']
        rubric=[{'criterion':key,'description':value} for key,value in pack['rubric'].items()]
        reading=READING+([{'title':'Decimal arithmetic','url':'https://docs.python.org/3/library/decimal.html'}] if pack['level']=='advanced' else [])
        sections=[{'heading':heading,'text':text} for heading,text in [
            ('Learning objective',pack['objective']),('Before you begin',pack['prerequisites']),
            ('What it is and why it matters',pack['why']),('Understand the concept',pack['concept']),
            ('Worked example',pack['example']),('Guided exercise',pack['guided']),
            ('Independent challenge',pack['challenge'])]]
        lessons.append({'id':lesson_id,'version':1,'module_id':'python','submodule_id':'python-basics',
            'level':pack['level'],'title':pack['title'],'skill':pack['skill'],'minutes':20,
            'sections':sections,'takeaway':pack['objective'],'status':'complete',
            'runnable_code':pack['code'],'expected_output':pack['output'],
            'mini_project':{'title':'Apply it: a learning tracker','task':pack['project'],
                            'rubric':rubric,'question_id':lesson_id+'-project'},
            'further_reading':reading,'next_topic_ids':pack['next'],
            'prerequisite_topic_ids':[] if pack['level']=='beginner' else ['python-functions'] if pack['level'] in ('intermediate','advanced') else []})
        for suffix,prompt,criteria,reference in [
            ('check',pack['quiz'],pack['quiz_rubric'],pack['quiz_reference']),
            ('project',pack['project'],pack['rubric'],pack['reference'])]:
            questions.append({'id':lesson_id+'-'+suffix,'version':1,'module_id':'python',
                'submodule_id':'python-basics','topic_id':'python-basics','level':pack['level'],
                'skill':pack['skill'],'lesson_id':lesson_id,'prompt':prompt,'hint':pack['objective'],
                'criteria':list(criteria),'criterion_descriptions':criteria,'reference':reference,
                'activity':'mini_project' if suffix=='project' else 'concept_check'})
        quiz,quiz_rubric,quiz_reference,challenge_rubric,challenge_reference=TRANSFER[pack['level']]
        for suffix,prompt,criteria,reference,activity in [
            ('transfer',quiz,quiz_rubric,quiz_reference,'concept_check'),
            ('challenge',pack['challenge'],challenge_rubric,challenge_reference,'mini_project')]:
            questions.append({'id':lesson_id+'-'+suffix,'version':1,'module_id':'python',
                'submodule_id':'python-basics','topic_id':'python-basics','level':pack['level'],
                'skill':pack['skill'],'lesson_id':lesson_id,'prompt':prompt,'hint':pack['objective'],
                'criteria':list(criteria),'criterion_descriptions':criteria,'reference':reference,'activity':activity})
