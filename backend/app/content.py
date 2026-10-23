"""Versioned starter lessons used by the reader and tutor."""
LESSONS = [
    {'id': 'predictions', 'version': 1, 'title': 'A line that makes predictions', 'skill': 'Make predictions', 'minutes': 6,
     'sections': [
         {'heading': 'Start with a real question', 'text': 'Imagine estimating delivery time from distance. Distance is the input feature x. Delivery time in minutes is the target y. Linear regression uses a straight line to predict a numeric target.'},
         {'heading': 'Read the equation', 'text': 'predicted time = 10 + 2 × distance\n\nThe intercept, 10, is the predicted time at distance zero. The slope, 2, means the prediction increases by 2 minutes for each additional kilometer. The intercept may not have a useful real-world interpretation if zero is outside the data range.'},
         {'heading': 'Work through a prediction', 'text': 'For 3 kilometers: 10 + 2 × 3 = 16 minutes. This is a prediction, not a guarantee. Traffic and other factors affect actual times. These coefficients are supplied; training a model means learning coefficients from data.'},
         {'heading': 'Try explaining it', 'text': 'If distance increases from 3 to 4 kilometers, how does the predicted time change? Explain using the slope and its units.'}],
     'takeaway': 'A linear model combines an intercept and a slope to predict a numeric outcome.'},
    {'id': 'coefficients', 'version': 1, 'title': 'Understand what coefficients mean', 'skill': 'Interpret coefficients', 'minutes': 7,
     'sections': [
         {'heading': 'Direction and size', 'text': 'A positive slope increases the prediction as x increases. A negative slope decreases it. Units matter: minutes per kilometer in our delivery example.'},
         {'heading': 'Association is not causation', 'text': 'A fitted coefficient describes a relationship in the model. It does not prove that changing the input causes the target to change. Omitted variables and selection effects can affect the relationship.'},
         {'heading': 'More than one feature', 'text': 'With multiple features, a coefficient describes the prediction change for a one-unit change in that feature while other model inputs are held fixed. Correlated inputs can make estimates unstable.'},
         {'heading': 'Practice your explanation', 'text': 'In predicted price = 50000 + 200 × area, where price is dollars and area is square feet, explain the slope. What does the intercept predict, and when might that interpretation be unhelpful?'}],
     'takeaway': 'Interpret a coefficient with its units, context, and limitations.'},
    {'id': 'residuals', 'version': 1, 'title': 'Measure prediction errors', 'skill': 'Understand residuals', 'minutes': 8,
     'sections': [
         {'heading': 'Compare reality with the prediction', 'text': 'A residual is actual minus predicted value. If a delivery takes 19 minutes and the model predicts 16, the residual is +3 minutes. A positive residual means the model underpredicted.'},
         {'heading': 'Summarize errors', 'text': 'Mean squared error averages squared residuals. For residuals +3 and -1, MSE = (9 + 1) / 2 = 5 square minutes. Squaring prevents positive and negative errors from canceling and penalizes larger errors more strongly.'},
         {'heading': 'Measure generalization', 'text': 'Low training error does not establish performance on new data. Fit preprocessing only on training data. Use validation data for development and reserve a final test set for independent evaluation.'},
         {'heading': 'Check your understanding', 'text': 'A model predicts 20 minutes; the delivery takes 17. What is the residual? Did it overpredict or underpredict? Why also evaluate on unseen deliveries?'}],
     'takeaway': 'Residuals describe individual errors. Separate evaluation data helps measure generalization.'},
]

def find_lesson(lesson_id):
    return next((lesson for lesson in LESSONS if lesson['id'] == lesson_id), None)
