"""Deterministic, timestamp-based analytics. No computer-vision dependencies."""
from datetime import datetime, timedelta
from math import isfinite


def inside(point, polygon):
    x, y = point
    result = False
    j = len(polygon) - 1
    for i, (xi, yi) in enumerate(polygon):
        xj, yj = polygon[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            result = not result
        j = i
    return result


def validate_config(c):
    if not isinstance(c.get('zones'), dict) or not c['zones']:
        raise ValueError('Define at least one zone.')
    for name, polygon in c['zones'].items():
        if len(polygon) < 3 or any(len(p) != 2 or any(not isinstance(v, (int, float)) or not isfinite(v) or not 0 <= v <= 1 for v in p) for p in polygon):
            raise ValueError(f'{name}: use at least 3 normalized [x,y] vertices between 0 and 1.')
        area = sum(polygon[i][0]*polygon[(i+1)%len(polygon)][1] - polygon[(i+1)%len(polygon)][0]*polygon[i][1] for i in range(len(polygon)))
        if abs(area) < 1e-6:
            raise ValueError(f'{name}: polygon must have nonzero area.')
    if c.get('queue_zone') not in c['zones']:
        raise ValueError('queue_zone must name a configured zone.')
    g = c['gate']
    if g['axis'] not in ('x', 'y') or g['entry_direction'] not in (-1, 1):
        raise ValueError('Gate axis must be x/y; direction must be -1 or 1.')
    if not 0 < g['position'] < 1 or not 0 <= g['span'][0] < g['span'][1] <= 1:
        raise ValueError('Invalid gate position/span.')
    if not 0 < g.get('deadband', .015) < .2:
        raise ValueError('Gate deadband must be positive and below 0.2.')
    for key in ('lost_timeout_s', 'queue_alert_s'):
        if c[key] <= 0:
            raise ValueError(f'{key} must be positive.')
    if c['queue_alert_count'] < 1:
        raise ValueError('queue_alert_count must be at least 1.')
    return c


class Analytics:
    """One engine per video. Track IDs are local, anonymous and may fragment."""
    def __init__(self, config, start, run_id, source_type='video'):
        self.config = validate_config(config)
        self.start = datetime.fromisoformat(start)
        self.run_id, self.source_type = run_id, source_type
        self.tracks, self.events, self.visits, self.samples, self.positions = {}, [], [], [], []
        self.previous_t = None
        self.alert_since = None
        self.alert_active = False

    def timestamp(self, t):
        # Local wall time; timezone is explicitly recorded in metadata.
        return (self.start + timedelta(seconds=t)).isoformat(sep=' ', timespec='milliseconds')

    def event(self, t, kind, tid='', zone='', value=1):
        self.events.append(dict(run_id=self.run_id, source_type=self.source_type,
            timestamp=self.timestamp(t), seconds=round(t, 4), event=kind,
            track_id=tid, zone=zone, value=value))

    def close_visit(self, tid, state, zone, t, reason):
        opened = state['zones'].pop(zone)
        self.visits.append(dict(run_id=self.run_id, source_type=self.source_type,
            track_id=tid, zone=zone, entered_at=self.timestamp(opened['start']),
            exited_at=self.timestamp(t), duration_s=round(max(0, t-opened['start']), 4),
            left_censored=opened['left_censored'], right_censored=reason != 'zone_exit',
            end_reason=reason))

    def expire(self, t):
        for tid, state in list(self.tracks.items()):
            if t - state['last'] > self.config['lost_timeout_s']:
                for zone in list(state['zones']):
                    self.close_visit(tid, state, zone, state['last'], 'track_lost')
                del self.tracks[tid]

    def update(self, t, detections):
        """detections: [{id, x, y}] normalized bottom-centre foot points."""
        if not isfinite(t) or t < 0 or self.previous_t is not None and t <= self.previous_t:
            raise ValueError('Frame timestamps must be finite, nonnegative and strictly increasing.')
        ids = [int(d['id']) for d in detections]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate track ID in a frame.')
        if any(not isfinite(d[k]) or not 0 <= d[k] <= 1 for d in detections for k in ('x','y')):
            raise ValueError('Invalid normalized position.')
        self.expire(t)
        zone_counts = {z: 0 for z in self.config['zones']}
        g = self.config['gate']; ax = g['axis']; other = 'y' if ax == 'x' else 'x'
        for d in detections:
            tid = int(d['id'])
            new = tid not in self.tracks
            state = self.tracks.setdefault(tid, {'last': t, 'side': 0, 'anchor': None, 'zones': {}})
            delta = d[ax] - g['position']
            side = 1 if delta > g['deadband'] else -1 if delta < -g['deadband'] else 0
            if side:
                if state['side'] and state['side'] != side:
                    old = state['anchor']
                    fraction = (g['position'] - old[ax]) / (d[ax] - old[ax])
                    cross = old[other] + fraction * (d[other] - old[other])
                    if g['span'][0] <= cross <= g['span'][1]:
                        kind = 'entry' if side == g['entry_direction'] else 'exit'
                        self.event(t, kind, tid)
                state['side'], state['anchor'] = side, dict(d)
            for zone, poly in self.config['zones'].items():
                if inside((d['x'], d['y']), poly):
                    zone_counts[zone] += 1
                    if zone not in state['zones']:
                        state['zones'][zone] = {'start': t, 'left_censored': new}
                elif zone in state['zones']:
                    self.close_visit(tid, state, zone, t, 'zone_exit')
            state['last'] = t
            self.positions.append(dict(run_id=self.run_id, source_type=self.source_type,
                timestamp=self.timestamp(t), seconds=round(t,4), track_id=tid,
                x=round(d['x'],4), y=round(d['y'],4)))
        queue = zone_counts[self.config['queue_zone']]
        if queue >= self.config['queue_alert_count']:
            if self.alert_since is None:
                self.alert_since = t
            if not self.alert_active and t - self.alert_since >= self.config['queue_alert_s']:
                self.event(t, 'queue_alert', zone=self.config['queue_zone'], value=queue)
                self.alert_active = True
        else:
            self.alert_since, self.alert_active = None, False
        row = dict(run_id=self.run_id, source_type=self.source_type, timestamp=self.timestamp(t),
            seconds=round(t,4), visible_people=len(detections), queue_length=queue,
            queue_alert_active=int(self.alert_active))
        row.update({'zone_'+z: n for z, n in zone_counts.items()})
        self.samples.append(row)
        self.previous_t = t
        return row

    def finish(self):
        for tid, state in self.tracks.items():
            for zone in list(state['zones']):
                self.close_visit(tid, state, zone, state['last'], 'video_end')
