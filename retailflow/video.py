from pathlib import Path
import json
import time
import cv2
import numpy as np
from .engine import Analytics
from .export import export_run


def overlay(frame, config):
    h,w = frame.shape[:2]
    for name, poly in config['zones'].items():
        pts=np.array([[int(x*w),int(y*h)] for x,y in poly],dtype=np.int32)
        cv2.polylines(frame,[pts],True,(80,210,140),2)
        cv2.putText(frame,name,tuple(pts[0]),cv2.FONT_HERSHEY_SIMPLEX,.6,(80,210,140),2)
    g=config['gate']; a,b=g['span']; p=g['position']
    endpoints=((int(a*w),int(p*h)),(int(b*w),int(p*h))) if g['axis']=='y' else ((int(p*w),int(a*h)),(int(p*w),int(b*h)))
    cv2.line(frame,*endpoints,(50,180,255),3)
    return frame


def analyze_video(source, config, output, start, model_path='yolo11n.pt', confidence=.3,
                  device='cpu', max_seconds=300, progress=None, save_video=True):
    from ultralytics import YOLO
    import ultralytics
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    cap=cv2.VideoCapture(str(source)); writer=None
    if not cap.isOpened():
        raise ValueError('Video cannot be opened. Try an MP4 encoded with H.264.')
    fps=cap.get(cv2.CAP_PROP_FPS)
    if not np.isfinite(fps) or fps<=0:
        cap.release(); raise ValueError('Video has invalid FPS; re-encode to constant frame rate first.')
    total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    limit=min(total,int(max_seconds*fps)) if total>0 else int(max_seconds*fps)
    engine=Analytics(config,start,output.name)
    started=time.perf_counter(); n=0
    try:
        model=YOLO(model_path)  # Fresh tracker for every independent video.
        names=model.names
        person_classes=[int(i) for i,name in names.items() if name.lower()=='person']
        if not person_classes:
            raise ValueError('Selected model must contain a class named person.')
        while n<limit:
            ok, frame=cap.read()
            if not ok: break
            h,w=frame.shape[:2]
            result=model.track(frame,persist=True,tracker='bytetrack.yaml',classes=person_classes,
                               conf=confidence,device=device,verbose=False)[0]
            detections=[]
            boxes=result.boxes
            if boxes is not None and boxes.id is not None:
                for box,tid in zip(boxes.xyxy.cpu().tolist(),boxes.id.int().cpu().tolist()):
                    x1,y1,x2,y2=box
                    detections.append(dict(id=tid,x=float(np.clip((x1+x2)/2/w,0,1)),y=float(np.clip(y2/h,0,1))))
            row=engine.update(n/fps,detections)
            if save_video:
                if writer is None:
                    writer=cv2.VideoWriter(str(output/'annotated.avi'),cv2.VideoWriter_fourcc(*'MJPG'),fps,(w,h))
                    if not writer.isOpened(): raise ValueError('Could not create output video.')
                rendered=overlay(result.plot(),config)
                cv2.putText(rendered,f"Visible: {row['visible_people']} Queue-zone: {row['queue_length']}",(15,h-20),cv2.FONT_HERSHEY_SIMPLEX,.65,(255,255,255),2)
                writer.write(rendered)
            n+=1
            if progress and (n%20==0 or n==limit): progress(n/max(1,limit))
        if n==0: raise ValueError('No frames decoded.')
    finally:
        cap.release()
        if writer is not None: writer.release()
    elapsed=time.perf_counter()-started
    return export_run(engine,output,dict(model=model_path,confidence=confidence,device=device,
        ultralytics_version=ultralytics.__version__,fps=fps,frames_processed=n,
        processing_seconds=elapsed,processing_fps=n/elapsed,
        truncated_at_limit=n>=limit and total>limit),end_seconds=n/fps)
