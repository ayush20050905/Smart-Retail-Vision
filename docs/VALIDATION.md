# Validation performed

Build date: 1 October 2026. See BUILD_ENVIRONMENT.txt for the actual installed runtime versions. Tests ran on Linux/Python 3.12, not Windows.

## Passed

- 10 automated tests: directional counting with deadband jitter, finite gate span, initial partial visit and full re-entry duration, track loss and reset, one alert per sustained episode, empty exports, interval weighting across minute boundaries, invalid timestamps/config, video-end censoring, and all four Streamlit navigation sections.
- Compiled Python modules without syntax errors.
- Generated synthetic demo: 30 minutes / 1,800 observed seconds, 150 entry crossings, 14 queue-alert episodes. These are simulation outputs, not measured detection performance.
- Parsed the Tableau XML: five worksheets and one four-panel dashboard. Checked the TWBX ZIP and embedded CSV. This is structural validation only.
- Ran the real YOLO11n + ByteTrack → analytics → CSV → annotated-video pipeline on a two-second, 20-frame, 10 FPS test video built by repeating the official Ultralytics bus example image. Four people were tracked at peak; all 20 annotated output frames decoded successfully. This verifies inference and I/O wiring, not motion/counting accuracy on real store footage.
- The smoke inference took approximately 21.3 seconds including model initialization/download overhead on this environment. Do not use that number as a representative throughput benchmark.

## Not performed / requires your environment or data

- Tableau Desktop/Public opening and visual verification; advanced guide actions and calculations require local configuration.
- Windows installation execution. README commands are provided for Windows PowerShell.
- Custom retail training and held-out retail accuracy evaluation. No private store footage or labelled dataset was supplied.
- Real doorway-crossing/queue accuracy, IDF1/HOTA benchmarks, multi-camera operation, production scale/load tests or cloud deployment.

## Reproduce

Run `python -m pytest -q` inside your installed virtual environment. Regenerate the synthetic data with `python scripts/make_demo.py`, then the starter workbook with `python scripts/build_tableau.py`. Training and independent evaluation commands are in TRAINING.md.

The downloaded smoke-test image, model weights, temporary video and inference outputs are not bundled. The image source was https://raw.githubusercontent.com/ultralytics/assets/main/im/bus.jpg .
