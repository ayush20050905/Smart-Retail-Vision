"""Compare minute-level aggregate counts against independent manual annotations."""
import argparse
import csv
import json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--predicted',required=True); p.add_argument('--truth',required=True)
p.add_argument('--output',default='count_metrics.json')
a=p.parse_args()
def read(path):
    with open(path, newline='',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    keyed={r['minute']:r for r in rows}
    if len(keyed)!=len(rows): raise ValueError('Use one run only, with unique minute keys.')
    return keyed
pred,truth=read(a.predicted),read(a.truth)
if not truth: raise ValueError('Truth annotations are empty.')
if set(pred)!=set(truth): raise ValueError('Predicted/truth minute keys must match exactly. Do not silently drop missed intervals.')
metrics={}
for key in ('entries','exits'):
    errors=[float(pred[t][key])-float(truth[t][key]) for t in truth]
    metrics[key]={'MAE':sum(abs(e) for e in errors)/len(errors),'RMSE':(sum(e*e for e in errors)/len(errors))**.5,'bias':sum(errors)/len(errors)}
Path(a.output).write_text(json.dumps(metrics,indent=2)); print(json.dumps(metrics,indent=2))
