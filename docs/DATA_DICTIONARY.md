# Export data dictionary

All CSVs are UTF-8 with headers, including empty tables. One output folder represents one run. Times use the user-supplied local start time; timezone is stored in metadata.json.

| File | Grain | Interpretation |
|---|---|---|
| minute_metrics.csv | One run × local minute | entries/exits: directional crossings; queue_alerts: new episodes; observed_seconds: video duration; person_seconds/queue_person_seconds: interval-weighted counts; peak_visible/peak_queue: maximum sampled counts; alert_seconds: active alert duration |
| events.csv | One event | timestamp, seconds, event (entry/exit/queue_alert), track_id when applicable, zone, value (1 crossing or crowd count at alert trigger) |
| samples.csv | One processed frame | visible_people, queue_length, queue_alert_active, zone_<name> counts |
| zone_visits.csv | One track-zone visit | entered_at, exited_at, duration_s, censor flags, end_reason (zone_exit, track_lost, video_end) |
| positions.csv | One track × observed frame | normalized x/y bottom-centre position; track_id; video timestamp |
| metadata.json | One run | model/settings, timezone, FPS, elapsed processing time, source label, limitations |

Every CSV contains run_id and source_type (video or synthetic_demo). IDs are scoped to a run. Repeat visits are separate rows. Do not physically join minute summaries to raw frame data and then sum counts.

Average visible people = SUM(person_seconds) / SUM(observed_seconds). Use the corresponding weighted expression for queue length. Do not average minute averages across unequal partial minutes. Censor flags identify incomplete visits; exclude both for complete-duration statistics. Brief tracking gaps can reduce visible counts while an existing visit remains open within the timeout.

Positions are kept in memory until completion. This prototype targets short single-camera research clips; hours of crowded footage can use substantial RAM/disk. There is no cross-camera deduplication or total-store occupancy initialization.
