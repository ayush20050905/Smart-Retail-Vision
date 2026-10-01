## Tableau analysis workflow

The application exports real CV measurements after video processing. The included `data/demo` files are synthetic and must stay labelled as a demonstration.

### Open the starter workbook

Open `tableau/RetailFlow.twb` in Tableau Desktop or Tableau Public Desktop. If prompted to locate the data, select `data/demo/minute_metrics.csv`. The starter contains footfall, visible-person, queue and alert views. The XML workbook is generated programmatically; it has not been opened in Tableau in the build environment. If your Tableau version rejects it, the steps below reproduce the views directly from CSV.

### Connect your own results

1. In the Python app, process a video and download the Tableau CSV bundle, or locate `outputs/<run>/`.
2. In Tableau choose **Connect → Text file → minute_metrics.csv**. Tableau supports CSV through the Text File connector.
3. Set `minute` to Date & Time, `date` to Date, counts to whole numbers and durations to decimals. Keep run, store, camera and source type as dimensions.
4. Replace the starter workbook connection with the new CSV (Edit Connection). Refresh after changing the file. Processing does not automatically push updates to Tableau Cloud.
5. Add `zone_visits.csv` and `positions.csv` as **separate data sources** for the advanced sheets. Do not physically join raw visits/positions to minute metrics: different row grains would multiply the counts.
6. Use one recording per dashboard initially. For multiple non-overlapping recordings, union identical CSV schemas and retain `run_id`. Overlapping camera views cannot be added to infer unique shoppers.

### Calculated fields — minute_metrics data source

Create each field with the exact name and formula below. If Tableau prettifies headers (e.g. `Person Seconds`), insert the matching field from its data pane.

**Average Visible People**
```tableau
IF SUM([observed_seconds]) > 0 THEN
    SUM([person_seconds]) / SUM([observed_seconds])
END
```

**Average Queue Length**
```tableau
IF SUM([observed_seconds]) > 0 THEN
    SUM([queue_person_seconds]) / SUM([observed_seconds])
END
```

**Queue Alert Time %** — format as Percentage
```tableau
IF SUM([observed_seconds]) > 0 THEN
    SUM([alert_seconds]) / SUM([observed_seconds])
END
```

**Net Crossings**
```tableau
SUM([entries]) - SUM([exits])
```
This is net crossings, not current occupancy: initial occupancy and missed doorways are unknown.

**Five-Minute Average Entries** — table calculation, compute using minute ascending
```tableau
WINDOW_AVG(SUM([entries]), -4, 0)
```
This uses five rows; it represents five minutes only when each minute is present, within one run. Partial starting/ending minutes should be excluded for rate comparisons.

**Daily Entries LOD**
```tableau
{ FIXED [store_id], [date] : SUM([entries]) }
```
Use MIN or ATTR when displaying this repeated daily value, not SUM. Add `source_type`, `run_id`, and any filters that should constrain this result to **Context**. FIXED LOD calculations otherwise ignore ordinary dimension filters.

### Dashboard 1 — Operations overview (1200 × 800)

| Sheet | Columns | Rows / Marks | Purpose |
|---|---|---|---|
| Entry trend | minute, exact date continuous | SUM(entries), Line | Doorway entry pattern |
| Exit trend | minute, exact date continuous | SUM(exits), Line | Exit pattern |
| Visible people | minute, exact date continuous | Average Visible People, Line | Camera-visible traffic |
| Queue trend | minute, exact date continuous | Average Queue Length, Line | Queue-zone congestion |
| Queue peaks | minute, exact date continuous | MAX(peak_queue), Bar | Short crowding peaks |
| Alert episodes | minute, exact date continuous | SUM(queue_alerts), Bar | Sustained threshold alerts |

Add entry crossings, peak visible people, average queue length and alert count KPI sheets to the top. Add run, date/time, store and source-type filters to sheets using this source. Retain a visible SYNTHETIC DEMO label when using sample data.

### Dashboard 2 — Zone and queue behaviour

Connect `zone_visits.csv`. Set the two censor flags to Boolean. Each row is one observed track-zone visit, including repeat visits.

**Complete Duration Seconds**
```tableau
IF NOT [left_censored] AND NOT [right_censored] THEN [duration_s] END
```

**Queue Duration Seconds**
```tableau
IF [zone] = 'checkout' AND NOT [left_censored] AND NOT [right_censored]
THEN [duration_s] END
```

Build a horizontal bar chart: `zone` on Rows, `COUNT([track_id])` on Columns (visit count, not unique people). Build a box plot of Complete Duration Seconds by zone. Add median and 90th-percentile queue-zone durations:
```tableau
MEDIAN([Queue Duration Seconds])
```
```tableau
PERCENTILE([Queue Duration Seconds], 0.9)
```
If PERCENTILE is unsupported by your live connector, create a Tableau extract. Display the count of complete visits alongside duration statistics; sparse samples are not representative. Do not report zero when no complete visits exist.

Add an integer parameter **Long Visit Threshold** (default 60), then:
```tableau
IF [Complete Duration Seconds] >= [Long Visit Threshold] THEN 'Long visit'
ELSEIF ISNULL([Complete Duration Seconds]) THEN 'Partial visit'
ELSE 'Short visit' END
```
Use the field for colour and show the parameter control. Add a dashboard filter action from a zone bar to the visit-duration sheet. Configure `zone` as the selected field. These two sheets share the visits source; this avoids cross-source filter ambiguity.

### Dashboard 3 — Movement heatmap

Use `positions.csv`. Create `X Bin = FLOOR([x]*24)/24` and `Y Bin = FLOOR([y]*16)/16`. Put X Bin on Columns, Y Bin on Rows, mark Square, `COUNT([track_id])` on Color, and reverse the Y axis. Fix axes to 0–1. Use timestamp/run filters. Each mark represents **track samples**, not unique people or square metres. Frame rates must match before comparing sample intensity across runs.

### Meaningful advanced Tableau analysis

- LOD daily totals with explicit context filters.
- A five-minute moving average with correct addressing/partitioning.
- Parameter-driven visit classification.
- Zone-selection dashboard filter actions.
- Median/P90 durations with censor filtering.
- Add weekday/hour heatmaps only after collecting several days; the included demo lasts 30 minutes and cannot support weekly conclusions.

### Interpretation boundaries

No purchases, revenue, conversion, gender, emotion or customer identity are inferred. Those are not output fields. Billing data is needed for sales analytics. Queue presence may include staff or people passing through; position the zone narrowly and manually verify a sample.

### Official references

- CSV connection: https://help.tableau.com/current/pro/desktop/en-us/examples_text.htm
- Calculated fields: https://help.tableau.com/current/pro/desktop/en-us/calculations_calculatedfields_create.htm
- FIXED and filters: https://help.tableau.com/current/pro/desktop/en-us/calculations_calculatedfields_lod_filters.htm
