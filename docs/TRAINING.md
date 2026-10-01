# Train and evaluate your own model

## 1. Prepare permitted footage
Record fixed-camera clips with known start time and constant FPS. Include entrances, exits, overlapping people, checkout queues and empty scenes. Label people including staff: the baseline does not distinguish staff from customers. Use a YOLO-compatible annotation tool. Every person box must cover the full visible person, consistently handling occluded people.

Split by original clip/day/camera before extracting images. Keep related frames in one split. Do not randomly split neighbouring frames: it causes leakage.

```
retail_dataset/
  images/train/*.jpg
  images/val/*.jpg
  images/test/*.jpg
  labels/train/*.txt
  labels/val/*.txt
  labels/test/*.txt
```

Each label file shares the image stem. Each row contains `0 centre_x centre_y width height` with coordinates normalized to 0–1. Use an empty file for a background image. Copy `config/dataset.example.yaml` to `config/dataset.yaml` and set its absolute dataset path.

## 2. Train
From the project folder, with requirements installed:

```powershell
.\.venv\Scripts\python.exe scripts/train.py --data config/dataset.yaml --epochs 50 --device cpu --batch 4
```

CPU training can take substantial time. For a compatible NVIDIA GPU and CUDA-enabled PyTorch use `--device 0 --batch 8`. Install the correct PyTorch build using its official installation selector. Do not assume a GPU is available.

Weights are written under the training run printed by Ultralytics, commonly `runs/detect/retail_person/weights/best.pt`. Later runs receive distinct folders. The application accepts the actual weights path in its Model weights field.

## 3. Measure detection quality
Evaluate both models on the same untouched test split:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_detector.py --weights yolo11n.pt --data config/dataset.yaml --output baseline_metrics.json
.\.venv\Scripts\python.exe scripts/evaluate_detector.py --weights runs/detect/retail_person/weights/best.pt --data config/dataset.yaml --output finetuned_metrics.json
```

The COCO baseline contains many classes while the custom dataset has only person (class 0). Restrict the validation to person when comparing them (the supplied script uses `classes=[0]`). Detector metrics do not evaluate track identity or queue timing.

## 4. Measure business-event accuracy
Create `truth_counts.csv` with columns `minute,entries,exits`. Copy the minute keys from one prediction export but manually count the footage independently. Include intervals with zero counts. Do not fill truth with predictions.

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_counts.py --predicted outputs/my_run/minute_metrics.csv --truth truth_counts.csv
```

For queue/time quality, independently annotate queue counts and complete zone visits on the same clip. Compare matched visitors manually; track IDs are not guaranteed stable. Record missed detections, ID switches and partial visits. No labelled retail dataset or training results are supplied; report metrics only after running this workflow.

## 5. Save reproducibility information
Keep training arguments, environment versions (`python -m pip freeze`), dataset version, split manifest, seed, weights, run config and detector/count metrics. The application saves inference settings and video FPS in each run's metadata.json.

Official documentation: https://docs.ultralytics.com/modes/train/ ; https://docs.ultralytics.com/modes/val/ ; https://docs.ultralytics.com/modes/track/ ; https://pytorch.org/get-started/locally/
