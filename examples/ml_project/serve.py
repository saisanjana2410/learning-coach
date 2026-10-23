"""Serve the trusted local artifact produced by train.py."""
import hashlib
import json
from pathlib import Path
import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field, ConfigDict

class Delivery(BaseModel):
    model_config=ConfigDict(extra='forbid')
    distance_km: float=Field(ge=0,le=100,strict=True,allow_inf_nan=False)
    traffic_index: float=Field(ge=0,le=1,strict=True,allow_inf_nan=False)

def create_app(artifact_dir):
    artifact_dir=Path(artifact_dir)
    manifest=json.loads((artifact_dir/'manifest.json').read_text(encoding='utf-8'))
    model_path=artifact_dir/'model.joblib'
    if hashlib.sha256(model_path.read_bytes()).hexdigest()!=manifest['artifact_sha256']:
        raise ValueError('Artifact hash differs from its manifest')
    if manifest['features']!=['distance_km','traffic_index']:
        raise ValueError('Unsupported feature contract')
    # Only load artifacts created locally by the trusted training script.
    pipeline=joblib.load(model_path)
    api=FastAPI(title='Delivery-time regression demo')

    @api.get('/health')
    def health():return {'status':'ok','model_version':manifest['model_version']}

    @api.post('/predict')
    def predict(payload:Delivery):
        row=pd.DataFrame([payload.model_dump()],columns=manifest['features'])
        return {'predicted_minutes':float(pipeline.predict(row)[0]),'model_version':manifest['model_version']}
    return api

def app():
    return create_app(Path(__file__).with_name('artifacts'))
