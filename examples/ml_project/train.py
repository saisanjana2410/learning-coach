"""A deterministic synthetic regression experiment; no dataset downloads or API calls."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURES=['distance_km','traffic_index']

def train(output,track=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(42)
    distance=rng.uniform(1,20,120)
    traffic=rng.uniform(0,1,120)
    target=10+2*distance+8*traffic+rng.normal(0,1.5,120)
    frame=pd.DataFrame({'distance_km':distance,'traffic_index':traffic,'minutes':target})
    frame.loc[:7,'distance_km']=np.nan
    development,test=train_test_split(frame,test_size=.2,random_state=42)
    training,validation=train_test_split(development,test_size=.25,random_state=42)
    candidates=[]
    for alpha in [.1,1.,10.]:
        model=Pipeline([('impute',SimpleImputer()),('scale',StandardScaler()),('model',Ridge(alpha=alpha))])
        model.fit(training[FEATURES],training['minutes'])
        error=mean_absolute_error(validation['minutes'],model.predict(validation[FEATURES]))
        candidates.append((float(error),alpha,model))
    validation_mae,alpha,winner=min(candidates,key=lambda item:item[0])
    baseline=DummyRegressor(strategy='mean').fit(training[FEATURES],training['minutes'])
    report={
        'dataset':'synthetic-deliveries-v1','seed':42,'features':FEATURES,
        'units':{'distance_km':'kilometers','traffic_index':'0 to 1','prediction':'minutes'},
        'train_rows':len(training),'validation_rows':len(validation),'test_rows':len(test),
        'alpha':alpha,'validation_mae':validation_mae,
        'test_mae':float(mean_absolute_error(test['minutes'],winner.predict(test[FEATURES]))),
        'baseline_test_mae':float(mean_absolute_error(test['minutes'],baseline.predict(test[FEATURES]))),
        'sklearn_version':sklearn.__version__,
        'environment':{'python':platform.python_version(),'numpy':np.__version__,
                       'pandas':pd.__version__,'scikit_learn':sklearn.__version__,'joblib':joblib.__version__},
        'training_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'selection_policy':'Choose alpha on validation MAE; test once after selection; no train+validation refit.',
    }
    version=hashlib.sha256(json.dumps(report,sort_keys=True).encode()).hexdigest()[:12]
    report['model_version']=version
    joblib.dump(winner,output/'model.joblib')
    report['artifact_sha256']=hashlib.sha256((output/'model.joblib').read_bytes()).hexdigest()
    (output/'manifest.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    if track:
        import mlflow
        mlflow.set_tracking_uri(f'sqlite:///{(output.resolve()/"experiments.db").as_posix()}')
        mlflow.set_experiment('delivery-time-demo')
        with mlflow.start_run():
            mlflow.log_params({'alpha':alpha,'seed':42,'dataset':report['dataset'],'model_version':version})
            mlflow.log_metrics({k:report[k] for k in ['validation_mae','test_mae','baseline_test_mae']})
            mlflow.log_artifact(str(output/'manifest.json'))
            mlflow.log_artifact(str(output/'model.joblib'))
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default=str(Path(__file__).with_name('artifacts')))
    parser.add_argument('--track',action='store_true',help='Optional local MLflow tracking; install mlflow first.')
    args=parser.parse_args()
    print(json.dumps(train(args.output,args.track),indent=2))
