# Delivery-time prediction project

Build a local regression pipeline and a validated FastAPI prediction service. The 120-row dataset is generated deterministically from a synthetic relationship with noise. It is an engineering exercise, not evidence about actual delivery operations. No dataset download, OpenAI call, credentials or paid service is required.

## Setup

Use Python 3.11 or newer. In this folder, create a virtual environment and install the requirements:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python train.py
python -m uvicorn serve:app --factory --host 127.0.0.1 --port 8002
```

Open `http://127.0.0.1:8002/docs` to try the API. A valid request to `POST /predict` is:

```json
{"distance_km": 5.0, "traffic_index": 0.4}
```

The response includes `predicted_minutes` and `model_version`. `/health` identifies the loaded version. Stop the service with Ctrl+C.

## Milestones

1. **Python/data:** inspect the ordered features, target and missing values. Preserve valid zeros and keep rows aligned.
2. **Baseline:** understand a constant training-mean predictor and MAE in minutes.
3. **Training:** use 72 training rows, 24 validation rows and 24 held-out test rows. Fit imputation/scaling/model on training only. Select alpha by validation MAE; evaluate the selected model on test after selection. The script deliberately does not refit on training plus validation.
4. **Artifacts:** inspect `artifacts/manifest.json` and `artifacts/model.joblib`. The manifest records settings, split counts, feature order/units, versions, metrics and the artifact hash. Record your own Git revision and a frozen dependency environment alongside the report when extending the project.
5. **Serving:** compare an offline pipeline prediction with the endpoint on the same ordered features. Check negative distances, boolean/string values, missing fields and unexpected fields are rejected.
6. **Operations:** propose error/latency monitoring, input-quality checks, delayed labeled MAE evaluation, a meaningful minimum sample/window policy and a compatible previous pipeline/schema for rollback.

Keep these as evidence-backed milestones: running a script alone does not establish mastery. Submit your code and reasoning in the app's applied practice for rubric feedback. The app reviews text and does not run learner code.

## Experiment tracking extension

The manifest provides a basic local experiment record. To try MLflow, install it separately and rerun with local tracking:

```powershell
python -m pip install mlflow
python train.py --track
```

This optional extension logs parameters, metrics and artifacts to a local SQLite tracking store in the output directory. It is not required for the baseline project checks. Avoid selecting parameters by repeatedly inspecting final test scores.

## Artifact contract

Feature order is `distance_km`, then `traffic_index`. The API accepts finite numeric distance in [0, 100] kilometers and traffic in [0, 1], rejects booleans/strings/unexpected fields, and returns minutes. Some allowed API inputs extrapolate beyond this toy training range; range validation is not a guarantee of model quality.

Only deserialize your controlled locally trained joblib artifact. A checksum detects changes relative to the manifest; it is not authentication or proof of trust. Keep manifests/artifacts from the same run together. Before production use, evaluate on representative real data, validate dependencies and develop a real operational/release plan.

References: [scikit-learn pipelines](https://scikit-learn.org/stable/modules/compose.html), [model persistence](https://scikit-learn.org/stable/model_persistence.html), [FastAPI bodies](https://fastapi.tiangolo.com/tutorial/body/), [MLflow tracking](https://mlflow.org/docs/latest/ml/tracking/).
