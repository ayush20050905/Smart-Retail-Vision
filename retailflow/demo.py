"""Synthetic tracks exercise analytics only; no simulated detection accuracy."""
import random
from pathlib import Path
from .engine import Analytics
from .export import export_run


def generate(config, folder, minutes=30, seed=17):
    rng=random.Random(seed)
    engine=Analytics(config,'2026-10-01T10:00:00',Path(folder).name,'synthetic_demo')
    people=[]
    for tid in range(minutes*5):
        born=rng.uniform(0,max(1,minutes*60-100))
        shop=rng.uniform(15,65); wait=rng.uniform(10,70)
        people.append((tid,born,shop,wait,rng.choice([.25,.62])))
    for t in range(minutes*60):
        ds=[]
        for tid,born,shop,wait,x in people:
            age=t-born
            if age<0: continue
            if age<8: px,py=x,.96-age*.07
            elif age<8+shop: px,py=x,.4
            elif age<16+shop:
                f=(age-8-shop)/8; px,py=x+(.89-x)*f,.4
            elif age<16+shop+wait: px,py=.89,.4
            elif age<26+shop+wait: px,py=.89,.4+(age-16-shop-wait)*.058
            else: continue
            ds.append(dict(id=tid,x=px,y=py))
        engine.update(float(t),ds)
    return export_run(engine,folder,dict(note='Synthetic trajectories; not measured model performance.'),end_seconds=minutes*60)
