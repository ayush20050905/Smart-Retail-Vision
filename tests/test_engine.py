import copy
import csv
import json
from pathlib import Path
import pytest
from retailflow.engine import Analytics, validate_config
from retailflow.export import export_run

BASE=json.loads((Path(__file__).resolve().parents[1]/'config/store.json').read_text())
def make(): return Analytics(copy.deepcopy(BASE),'2026-10-01T10:00:00','test')
def d(y,x=.25,tid=1): return {'id':tid,'x':x,'y':y}

def test_direction_and_deadband():
    a=make()
    for t,y in enumerate([.9,.785,.775,.784,.75,.77,.79,.9]): a.update(t*.1,[d(y)])
    assert [e['event'] for e in a.events]==['entry','exit']

def test_gate_span_does_not_count_outside_door():
    a=make(); a.update(0,[d(.9,.01)]); a.update(.1,[d(.6,.01)])
    assert not a.events

def test_seen_first_inside_is_censored_but_reentry_complete():
    a=make(); a.update(0,[d(.4)]); a.update(.2,[d(.7)])
    a.update(.4,[d(.4)]); a.update(.8,[d(.7)])
    assert a.visits[0]['left_censored'] is True
    assert a.visits[1]['left_censored'] is False
    assert a.visits[1]['right_censored'] is False
    assert a.visits[1]['duration_s']==.4

def test_lost_track_closes_at_last_seen_and_does_not_cross_gap():
    a=make(); a.update(0,[d(.4)]); a.update(.2,[d(.4)]); a.update(2,[])
    assert a.visits[0]['duration_s']==.2
    assert a.visits[0]['end_reason']=='track_lost'
    a.update(3,[d(.9)]); assert not a.events

def test_queue_alert_is_one_per_sustained_episode():
    a=make(); ds=[d(.4,.89,i) for i in range(3)]
    for t in range(9): a.update(t,ds)
    assert len(a.events)==1 and a.events[0]['event']=='queue_alert'
    a.update(9,[])
    for t in range(10,17): a.update(t,ds)
    assert len(a.events)==2

def test_empty_run_has_headers(tmp_path):
    export_run(make(),tmp_path)
    for name in ('events','positions','zone_visits','minute_metrics'):
        assert (tmp_path/f'{name}.csv').read_text().strip()

def test_weights_and_minute_boundary(tmp_path):
    a=make(); a.update(0,[d(.9)]); a.update(59,[d(.9),d(.9,.3,2)])
    export_run(a,tmp_path,end_seconds=61)
    rows=list(csv.DictReader((tmp_path/'minute_metrics.csv').open()))
    assert len(rows)==2
    assert float(rows[0]['person_seconds'])==61
    assert float(rows[0]['observed_seconds'])==60
    assert float(rows[1]['person_seconds'])==2
    assert sum(float(r['observed_seconds']) for r in rows)==61

def test_timestamp_and_config_validation():
    a=make(); a.update(0,[])
    with pytest.raises(ValueError): a.update(0,[])
    with pytest.raises(ValueError): a.update(1,[d(.5,tid=1),d(.6,tid=1)])
    bad=copy.deepcopy(BASE); bad['queue_zone']='absent'
    with pytest.raises(ValueError): validate_config(bad)

def test_video_end_is_censored():
    a=make(); a.update(0,[d(.7)]); a.update(.2,[d(.4)]); a.update(.5,[d(.4)]); a.finish()
    assert a.visits[0]['duration_s']==.3
    assert a.visits[0]['right_censored'] is True
