"""Fine-tune person detection; tracking itself is not trained by this script."""
import argparse
from ultralytics import YOLO
p=argparse.ArgumentParser()
p.add_argument('--data',required=True,help='YOLO dataset YAML with class person')
p.add_argument('--model',default='yolo11n.pt')
p.add_argument('--epochs',type=int,default=50)
p.add_argument('--device',default='cpu'); p.add_argument('--batch',type=int,default=8)
a=p.parse_args()
YOLO(a.model).train(data=a.data,epochs=a.epochs,imgsz=640,batch=a.batch,device=a.device,seed=42,deterministic=True,project='runs/detect',name='retail_person',exist_ok=False)
