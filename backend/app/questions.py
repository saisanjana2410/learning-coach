"""Versioned questions. Rubrics stay on the server until assessment is accepted."""
QUESTIONS = [
    {'id':'slope-delivery','skill':'Interpret coefficients','lesson_id':'coefficients','prompt':'A model predicts delivery time in minutes as 10 + 2 × distance in kilometers. Explain the slope and intercept, including their units.','hint':'Consider a one-kilometer increase and a distance of zero.','criteria':['slope','intercept'],'reference':'Slope: 2 minutes per kilometer; each extra kilometer increases the prediction by 2 minutes. Intercept: predicted 10 minutes at zero kilometers, which may not be meaningful outside the observed range.'},
    {'id':'slope-price','skill':'Interpret coefficients','lesson_id':'coefficients','prompt':'Predicted price in dollars = 50000 + 200 × area in square feet. Explain the coefficient 200 and why interpreting 50000 needs care.','hint':'Use dollars per square foot and consider whether zero area occurs in the data.','criteria':['slope','intercept'],'reference':'Prediction increases by 200 dollars for an extra square foot; 50000 is the prediction at zero area, potentially outside the meaningful data range.'},
    {'id':'predict-delivery','skill':'Make predictions','lesson_id':'predictions','prompt':'Using predicted minutes = 10 + 2 × distance in kilometers, predict the time for 4 kilometers. Show your calculation and explain whether the result is guaranteed.','hint':'Substitute 4 for distance; predictions can differ from actual observations.','criteria':['calculation','uncertainty'],'reference':'10 + 2 × 4 = 18 minutes. Actual delivery time is not guaranteed because the model omits other factors and has error.'},
    {'id':'predict-price','skill':'Make predictions','lesson_id':'predictions','prompt':'Predicted price in dollars = 100 + 3 × size. Calculate the prediction at size 5 and explain why an actual price could differ.','hint':'Substitute size into the equation and distinguish prediction from observation.','criteria':['calculation','uncertainty'],'reference':'100 + 3 × 5 = 115 dollars; actual values can differ because a fitted model has residual error and omits other influences.'},
    {'id':'residual-positive','skill':'Understand residuals','lesson_id':'residuals','prompt':'A model predicts 16 minutes, but delivery takes 19 minutes. Calculate the residual using actual minus predicted and explain whether the model overpredicted or underpredicted.','hint':'Use actual minus predicted. A prediction below the actual value is an underprediction.','criteria':['calculation','interpretation'],'reference':'19 - 16 = +3 minutes; the model underpredicted by 3 minutes.'},
    {'id':'residual-negative','skill':'Understand residuals','lesson_id':'residuals','prompt':'A model predicts 20 minutes, but delivery takes 17 minutes. Calculate the residual and explain its sign.','hint':'Use actual minus predicted, keeping the sign.','criteria':['calculation','interpretation'],'reference':'17 - 20 = -3 minutes; the negative residual means the model overpredicted by 3 minutes.'},
    {'id':'mse','skill':'Measure prediction error','lesson_id':'residuals','prompt':'Two residuals are +3 and -1 minutes. Calculate mean squared error and explain why averaging the raw residuals is not a good measure of error magnitude.','hint':'Square each residual, then take the mean.','criteria':['calculation','interpretation'],'reference':'MSE = (9 + 1)/2 = 5 square minutes. Raw signed residuals can cancel and hide error magnitude.'},
    {'id':'mse-fresh','skill':'Measure prediction error','lesson_id':'residuals','prompt':'Residuals are +2 and -2 minutes. Calculate MSE and compare it with the mean signed residual.','hint':'Compare the average of squares with the average of signed values.','criteria':['calculation','interpretation'],'reference':'MSE is 4 square minutes; mean signed residual is 0 minutes despite nonzero errors, because signs cancel.'},
    {'id':'evaluation','skill':'Evaluate on unseen data','lesson_id':'residuals','prompt':'Your regression model has very low training error. Does this establish performance on new data? Explain how you would evaluate it and avoid preprocessing leakage.','hint':'Consider a held-out split and where preprocessing parameters are learned.','criteria':['generalization','leakage'],'reference':'Training error does not establish generalization. Evaluate on held-out data; fit preprocessing only on training data, then transform the held-out data without refitting.'},
    {'id':'evaluation-fresh','skill':'Evaluate on unseen data','lesson_id':'residuals','prompt':'A developer scales the entire dataset before splitting train and test data, then reports test error. What is wrong and how would you fix the process?','hint':'Ask which observations influenced the scaler before splitting.','criteria':['generalization','leakage'],'reference':'The held-out data influenced preprocessing, causing leakage. Split first, fit scaler on train only, transform test, and evaluate without tuning on the final test set.'},
]

# The role interview spans several starter domains. Topic practice remains scoped.
QUESTIONS.extend([
    {'id':'python-mutable','topic_id':'python','skill':'Python data handling','lesson_id':'predictions',
     'prompt':'Why is a mutable list a risky default argument in a Python function? Explain a safer pattern.',
     'hint':'Think about when default arguments are evaluated.','criteria':['shared_state','safe_default'],
     'reference':'Defaults are evaluated once when the function is defined, so calls share and mutate the same list. Use None as the default and create a new list inside the function when the argument is None.'},
    {'id':'python-copy','topic_id':'python','skill':'Python data handling','lesson_id':'predictions',
     'prompt':'How do shallow and deep copies differ for a nested Python list, and why does this matter when preparing data?',
     'hint':'Consider whether inner objects are shared.','criteria':['nested_objects','consequence'],
     'reference':'A shallow copy creates a new outer list but shares inner objects; a deep copy recursively copies nested objects. Mutating a shared nested list can unexpectedly alter the original data.'},
    {'id':'sql-group','topic_id':'sql','skill':'SQL aggregation','lesson_id':'residuals',
     'prompt':'Explain WHERE versus HAVING when counting orders per customer. How would you keep only customers with more than five orders?',
     'hint':'One filter operates before grouping, one after.','criteria':['filter_stage','group_filter'],
     'reference':'WHERE filters rows before grouping. HAVING filters groups after aggregation. GROUP BY customer_id HAVING COUNT(*) > 5 keeps customers with more than five orders.'},
    {'id':'sql-count','topic_id':'sql','skill':'SQL aggregation','lesson_id':'residuals',
     'prompt':'How do COUNT(*) and COUNT(column) differ when column values can be NULL? Give an example.',
     'hint':'Consider which rows are counted.','criteria':['null_handling','example'],
     'reference':'COUNT(*) counts every row, while COUNT(column) counts only non-NULL values. For values 1, NULL, 2 the counts are 3 and 2 respectively.'},
    {'id':'classification-imbalance','topic_id':'ml-foundations','skill':'Classification metrics','lesson_id':'residuals',
     'prompt':'Why can accuracy mislead when only 1% of examples are positive? Explain which other metrics you would inspect.',
     'hint':'Consider a model that always predicts negative.','criteria':['baseline','metrics'],
     'reference':'Always predicting negative achieves 99% accuracy but zero positive recall. Inspect precision, recall, confusion matrix and metrics such as PR AUC depending on the cost of false positives and negatives.'},
    {'id':'classification-tradeoff','topic_id':'ml-foundations','skill':'Classification metrics','lesson_id':'residuals',
     'prompt':'Define precision and recall for a positive class and explain a practical tradeoff when changing the decision threshold.',
     'hint':'Distinguish predicted positives from actual positives.','criteria':['definitions','tradeoff'],
     'reference':'Precision is TP/(TP+FP); recall is TP/(TP+FN). Lowering a decision threshold usually increases recall while potentially lowering precision by admitting more false positives. Choose the operating point based on error costs.'},
])

def public_question(question):
    return {k: question[k] for k in ('id','skill','lesson_id','prompt','module_id','submodule_id','level') if k in question}
