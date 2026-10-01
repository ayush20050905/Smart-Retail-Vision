import argparse
import json
from pathlib import Path
from ultralytics import YOLO
p=argparse.ArgumentParser()
p.add_argument('--weights',required=True); p.add_argument('--data',required=True)
p.add_argument('--device',default='cpu'); p.add_argument('--output',default='detector_metrics.json')
a=p.parse_args()
m=YOLO(a.weights).val(data=a.data,split='test',classes=[0],device=a.device,imgsz=640)
Path(a.output).write_text(json.dumps(dict(weights=a.weights,data=a.data,split='test',precision=float(m.box.mp),recall=float(m.box.mr),mAP50=float(m.box.map50),mAP50_95=float(m.box.map)),indent=2))
print('Saved:',a.output)
