import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

SCHEMAS = {
    'events': ['run_id','source_type','timestamp','seconds','event','track_id','zone','value'],
    'zone_visits': ['run_id','source_type','track_id','zone','entered_at','exited_at','duration_s','left_censored','right_censored','end_reason'],
    'positions': ['run_id','source_type','timestamp','seconds','track_id','x','y'],
}


def write_csv(path, rows, fields):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


def export_run(engine, folder, metadata=None, end_seconds=None):
    """Weight frame observations by their actual time interval, split at minute boundaries."""
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    engine.finish()
    for name, rows in [('events',engine.events),('zone_visits',engine.visits),('positions',engine.positions)]:
        write_csv(folder / (name+'.csv'), rows, SCHEMAS[name])
    sample_fields = ['run_id','source_type','timestamp','seconds','visible_people','queue_length','queue_alert_active'] + ['zone_'+z for z in engine.config['zones']]
    write_csv(folder/'samples.csv', engine.samples, sample_fields)
    buckets = defaultdict(lambda: dict(observed_seconds=0., person_seconds=0., queue_person_seconds=0., peak_visible=0, peak_queue=0, entries=0, exits=0, queue_alerts=0, alert_seconds=0.))
    for i, row in enumerate(engine.samples):
        begin = datetime.fromisoformat(row['timestamp'])
        if i+1 < len(engine.samples):
            end = datetime.fromisoformat(engine.samples[i+1]['timestamp'])
        elif end_seconds is not None:
            end = engine.start + timedelta(seconds=end_seconds)
        else:
            end = begin
        while begin < end:
            minute = begin.replace(second=0, microsecond=0)
            boundary = min(end, minute+timedelta(minutes=1))
            dt = (boundary-begin).total_seconds(); b = buckets[minute]
            b['observed_seconds'] += dt
            b['person_seconds'] += dt*row['visible_people']
            b['queue_person_seconds'] += dt*row['queue_length']
            b['alert_seconds'] += dt*row['queue_alert_active']
            b['peak_visible'] = max(b['peak_visible'],row['visible_people'])
            b['peak_queue'] = max(b['peak_queue'],row['queue_length'])
            begin = boundary
    for row in engine.events:
        minute = datetime.fromisoformat(row['timestamp']).replace(second=0,microsecond=0)
        key = {'entry':'entries','exit':'exits','queue_alert':'queue_alerts'}[row['event']]
        buckets[minute][key] += 1
    rows = []
    for minute, b in sorted(buckets.items()):
        rows.append(dict(run_id=engine.run_id, source_type=engine.source_type,
            store_id=engine.config['store_id'],camera_id=engine.config['camera_id'],
            minute=minute.isoformat(sep=' '),date=minute.date().isoformat(),hour=minute.hour,
            **{k:round(v,4) if isinstance(v,float) else v for k,v in b.items()}))
    fields=['run_id','source_type','store_id','camera_id','minute','date','hour','observed_seconds','person_seconds','queue_person_seconds','peak_visible','peak_queue','entries','exits','queue_alerts','alert_seconds']
    write_csv(folder/'minute_metrics.csv', rows, fields)
    info = dict(run_id=engine.run_id,source_type=engine.source_type,config=engine.config,
        start_time=engine.start.isoformat(), frame_samples=len(engine.samples),
        timestamp_basis='video frame index / FPS; wall clock start supplied by user',
        duration_basis='frame interval weighted; last interval requires video end',
        limitations=['IDs are per-video tracks, not unique customers.',
            'Visible people and queue-zone people include staff.',
            'Queue-zone duration is a proxy, not verified waiting time.',
            'Camera perspective means heatmap is image-space, not floor-area density.'])
    info.update(metadata or {})
    (folder/'metadata.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
    return folder
