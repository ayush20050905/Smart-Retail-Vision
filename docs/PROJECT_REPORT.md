# RetailFlow AI: Smart Retail Vision Analytics

## Abstract
RetailFlow converts fixed-camera retail footage into anonymous people tracks and timestamped operational measurements. A YOLO detector localizes people, ByteTrack maintains short-term track identities, and a deterministic analytics layer estimates doorway crossings, zone activity and queue-zone congestion. Streamlit supports upload, camera-layout configuration, inspection and export. Tableau supports interactive operational analysis using minute summaries, visit records and position samples. The delivered model workflow supports fine-tuning and independent test evaluation; no trained-on-retail accuracy claim is made.

## Research question
How accurately can a lightweight person detector and tracker estimate store traffic and queue-zone activity under occlusion, variable lighting and camera perspective, and how can those observations support retail operational analysis?

## Objectives
1. Detect and track people in one camera stream.
2. Count directional doorway crossings with a deadband to reduce jitter.
3. Record track-zone visits and flag partially observed durations.
4. Trigger alerts only after a crowd threshold persists.
5. Export auditable event and aggregate tables for Tableau.
6. Compare baseline and fine-tuned detectors on held-out footage and manual operational annotations.

## Architecture
Video → OpenCV decoder → YOLO person boxes → ByteTrack IDs → normalized foot points → gate/zone analytics → CSV + JSON provenance → Streamlit/ Tableau.

The application processes every decoded frame. Timestamps use frame index divided by source FPS, not processing speed. Use constant-frame-rate footage; variable-frame-rate videos must be re-encoded first. Model loading and inference happen only when the user starts analysis. CPU mode is the default; CUDA is optional. The browser UI runs locally; no remote hosting is included.

## Deep learning methodology
- Baseline: COCO-pretrained YOLO11 nano, person class only.
- Custom training: fine-tune on person bounding boxes from permitted store footage. Split by recording/day/camera before extracting frames. Neighbouring frames from a single clip must not leak across training and test sets.
- Experiment: compare baseline and fine-tuned models with the same held-out videos, image size, confidence threshold, tracker, gate and zones.
- Training controls: fixed seed, deterministic option, explicit image size and batch size, separate validation and test data.
- ByteTrack associates detections over time; the supplied training script fine-tunes the detector, not the tracking algorithm.

## Dataset plan
Start with consented staged store-like videos filmed with friends/classmates, then add authorized store footage if available. Label diverse lighting, partial occlusion, staff/customer interactions and varied camera distances. A practical initial goal is 1,000–3,000 labelled frames from multiple sessions, with 70/15/15 train/validation/test splits at session level. This is a project planning target, not a guarantee of accuracy. Document consent, data provenance, licence, camera settings and split counts. No customer footage or retail training dataset is bundled.

YOLO label layout and commands are in TRAINING.md. Include empty-label frames so the detector learns background scenes. Avoid facial recognition, demographic inference or cross-camera identity linkage. Keep footage local and remove identifiers from presentation examples. Annotated videos retain visible people and therefore still need appropriate handling.

## Measurement definitions
- Entry/exit: a track crosses the finite doorway segment between opposite stable sides. No event is counted when a person is first detected on one side.
- Visible people: tracked detections in the current frame; not total store occupancy.
- Observed zone visit: continuous zone membership for one track. A track first observed inside a zone is left-censored; a lost track or recording end is right-censored.
- Duration: last known video-time span for that visit. Short tracking gaps within the timeout are bridged, introducing bounded uncertainty; longer gaps close at the last observation.
- Queue duration: the same zone-duration measurement for checkout, not actual service start or purchase completion.
- Queue alerts: one event per sustained crowding episode, resetting only after count drops below threshold.
- Heatmap: sampled image-space presence; perspective and FPS affect intensity.

## Evaluation plan
| Layer | Metric | Ground truth |
|---|---|---|
| Detection | precision, recall, mAP50, mAP50–95 | Held-out person bounding boxes |
| Tracking | ID switches, IDF1/HOTA (optional external evaluation) | Manually labelled persistent IDs |
| Crossings | minute MAE/RMSE, total bias | Independent manual entry/exit counts |
| Zone duration | MAE on matched complete visits | Manually marked zone entry/exit times |
| Queue occupancy | frame MAE | Manually counted queue-zone occupants |
| Alerts | true/false/missed alert episodes | Manual sustained-threshold intervals |
| Runtime | processing FPS and elapsed seconds | Run metadata on stated hardware |

Detection/count evaluation scripts are included. Full IDF1/HOTA and matched-event evaluation require external annotations/tooling and are not implemented. Do not claim tracking benchmark performance from the detector validation metrics. Choose success criteria before evaluating (for example a maximum acceptable crossing-count error), then report actual results whether or not they meet the target.

## Ablation ideas
Compare pretrained versus fine-tuned weights; confidence 0.25 versus 0.40; deadband 0.01 versus 0.03; timeout 0.5 versus 1.0 seconds; bright versus low-light clips. Change one factor at a time and retain identical test footage. Avoid tuning repeatedly on the test set.

## Tableau decisions supported
Identify busy intervals, compare zone activity, investigate queue spikes and review staff allocation opportunities. Charts should lead to hypotheses, not automated staffing or customer-attribute claims. A zone with high dwell time may indicate interest or confusion; video alone cannot distinguish those explanations.

## Demonstration sequence
1. Show labelled synthetic dashboard and explain why it is not a performance result.
2. Upload a short authorized video and preview gate/zone placement.
3. Run person detection/tracking and inspect annotated output.
4. Download CSVs and open the Tableau workbook.
5. Demonstrate a time filter, zone filter action and visit-threshold parameter.
6. Present measured baseline-versus-fine-tuned results and failure examples after completing training/evaluation.

## Deliverable status
The source application, deterministic analytics, synthetic demo and training/evaluation scripts are provided. Retail-specific training needs your footage and labels. Tableau is not installed in the build environment, so the workbook requires local opening and inspection. This is an educational single-camera prototype, not a deployed production surveillance system.
