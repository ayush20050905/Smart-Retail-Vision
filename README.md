# RetailFlow AI — Smart Retail Vision Analytics

A local end-to-end educational project combining **deep learning (YOLO), computer vision (OpenCV + ByteTrack), operational analytics and Tableau**.

## What you can do
- Upload a store video and preview gate/zone placement.
- Detect and track people, count directional entry/exit crossings.
- Measure observed zone visits, queue-zone presence and sustained queue alerts.
- Inspect charts, export results and download annotated video.
- Open a Tableau starter workbook and build advanced analysis using the included guide.
- Fine-tune your detector and evaluate it against held-out data.
- Run a labelled synthetic demo immediately, without model downloads or footage.

This is a runnable single-camera prototype. Custom retail training needs your labelled data. Queue duration is zone-presence time, not verified checkout waiting time. Track IDs do not identify unique customers.

## Windows / VS Code: start here

Install **64-bit Python 3.12** from https://www.python.org/downloads/ and select Add Python to PATH. Extract this ZIP, open the `retailflow` folder in VS Code and choose **Terminal → New Terminal**. Run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open **http://localhost:8501**. No account/password is required. The app binds to your local computer. These commands use the virtual-environment Python directly, avoiding PowerShell activation-policy issues. Initial dependencies/model downloads need internet and several GB of free disk space. CPU mode works without an NVIDIA GPU; this does not promise real-time inference.

On subsequent starts, double-click `start_windows.bat` or rerun the last command.

## Linux/macOS

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

The explicit CPU wheel command above is for Windows/Linux; on macOS use your platform's PyTorch installation instructions if needed.

## First demonstration

1. Start the app; Demo dashboard opens using the included synthetic trajectory data.
2. Switch to Analyze video and upload a short fixed-camera MP4 (30–60 seconds first).
3. Edit the zone/gate JSON to match your camera. Preview the overlay. All coordinates are normalized: x is left-to-right, y is top-to-bottom. Choose a gate segment across the doorway, not the entire store.
4. Enter the real recording start time in local wall-clock format. Config timezone describes it. The demo date is an example only. Use CPU and `yolo11n.pt` initially. The standard pretrained weights download on first real analysis.
5. Run analysis. Every decoded frame is processed. Results appear under Saved runs and in `outputs/<run>/`.
6. Open the downloaded AVI in a media player such as VLC. AVI is used for portability of writing; it is not embedded in the browser.
7. Open `tableau/RetailFlow_Demo.twbx` for the synthetic Tableau starter, or `tableau/RetailFlow.twb` and reconnect its data to a real `minute_metrics.csv` export.

The Tableau workbook was generated as XML and was not opened in a Tableau installation during the build. Follow `docs/TABLEAU_GUIDE.md` for connection repair, exact calculated fields, advanced dashboards and a CSV-only fallback.

## Project structure

| Path | Purpose |
|---|---|
| `app.py` | Streamlit upload/configuration/charts/export UI |
| `retailflow/video.py` | YOLO + ByteTrack video processing and annotations |
| `retailflow/engine.py` | Timestamp-driven crossing/zone/queue logic |
| `retailflow/export.py` | CSV tables and run metadata |
| `retailflow/demo.py` | Reproducible synthetic trajectories |
| `config/store.json` | Example normalized gate and zones |
| `scripts/train.py` | Detector fine-tuning |
| `scripts/evaluate_detector.py` | Test-split precision/recall/mAP |
| `scripts/evaluate_counts.py` | Minute-level crossing MAE/RMSE/bias |
| `scripts/analyze.py` | Command-line video analysis |
| `data/demo/` | Synthetic analytics data, ready to explore |
| `tableau/` | Starter workbook and packaged demo workbook |
| `docs/` | Tableau guide, training steps, report, data dictionary and test status |
| `tests/` | Analytics and Streamlit navigation tests |

## Configuration notes

- `gate.axis`: `y` for a horizontal line, `x` for vertical.
- `gate.position`: line coordinate; `span`: segment extent on the other axis.
- `entry_direction`: `-1` toward smaller coordinates, `1` toward larger coordinates.
- `deadband`: normalized margin around the line to suppress jitter.
- `zones`: named non-self-intersecting polygons. Overlapping zones count independently. Keep names simple (`checkout`, `apparel`, etc.).
- `queue_zone`: exact name of the queue polygon.
- `lost_timeout_s`: bridge brief track gaps; close longer gaps at last observation.
- `queue_alert_count` and `queue_alert_s`: minimum crowd and sustained duration.

Use a fixed camera and constant-frame-rate video. Foot-point membership is an approximation under perspective and occlusion. A line must cover the actual doorway; a shelf boundary is not an entrance.

## Command-line analysis

```powershell
.\.venv\Scripts\python.exe scripts/analyze.py "C:\Videos\store.mp4" --start "2026-10-01T10:00:00" --output outputs/my_run --seconds 60
```

Choose a fresh output directory per run. Use `--model path/to/best.pt` for fine-tuned weights and `--device 0` only with compatible CUDA PyTorch.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

See `docs/VALIDATION.md` for the actual checks performed in the build environment and their limitations. Optional detector/video smoke testing requires weights and test imagery to download.

## Academic workflow

Read `docs/TRAINING.md`, then `docs/PROJECT_REPORT.md`. Train and compare the baseline and fine-tuned model on the same held-out footage. Report measured metrics, hardware, failures and limitations. Never present the synthetic demo as model accuracy or real retail observations.

## Troubleshooting

- `No module named ...`: install requirements using the same `.venv` Python used to start the app.
- Weights download fails: download `yolo11n.pt` from the official Ultralytics release and enter its local path.
- Slow processing: begin with a 15-second clip or use a compatible GPU. Avoid skipping frames without adjusting tracking assumptions.
- No counts: inspect the annotated output and gate direction/span. Tracks must cross from one stable side to the other.
- No complete durations: the video may start/end while people are inside zones. Capture a longer clip; do not remove censor filters to inflate results.
- Poor detection: improve lighting/resolution or fine-tune on representative footage; do not assume the default detector meets your accuracy goal.
- Bad times: re-encode variable-frame-rate footage to constant FPS; specify the real start time.
- Tableau fields missing: use Text File connection, verify column types and refresh. Use the guide's field names or insert the equivalent field from the data pane.

## Dependencies and source documentation

- Ultralytics tracking: https://docs.ultralytics.com/modes/track/
- Training: https://docs.ultralytics.com/modes/train/
- Validation: https://docs.ultralytics.com/modes/val/
- Streamlit: https://docs.streamlit.io/
- Tableau CSV connector: https://help.tableau.com/current/pro/desktop/en-us/examples_text.htm
- Tableau FIXED filter order: https://help.tableau.com/current/pro/desktop/en-us/calculations_calculatedfields_lod_filters.htm

Dependencies retain their own licences. Review Ultralytics' AGPL-3.0/enterprise licensing before redistributing or commercially deploying an integrated product. No commercial deployment or public upload is performed by this project. Uploaded source videos are deleted from the temporary upload path after analysis; annotated outputs and coordinate logs persist locally until you delete them.
