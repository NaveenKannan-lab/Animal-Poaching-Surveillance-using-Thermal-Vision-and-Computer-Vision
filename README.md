<div align="center">

# 🛡️ PoachGuard

### Animal Poaching Surveillance Using Thermal Vision with CV

**Real-time thermal video analysis for detecting potential human–wildlife intrusion events in protected forest environments.**

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Fine--Tuned-7B3FF2?style=for-the-badge)
![Flask](https://img.shields.io/badge/Flask-Backend-000000?style=for-the-badge&logo=flask&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-Deep%20Learning-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-Frontend-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

</div>

---

## 1. Project Title

### PoachGuard — Animal Poaching Detection System

**Tagline:**  
*Detect threats. Capture evidence. Protect wildlife.* - The project was developed to explore AI-based wildlife surveillance and automated anti-poaching support.

PoachGuard is an AI-powered surveillance platform developed to detect potential poaching activity from thermal video streams. It combines thermal image enhancement, fine-tuned YOLOv8 object detection, event-based threat analysis, real-time video streaming, alert generation, and evidence-frame capture within a unified web application.

---

## 2. About the Project

### 2.1 What It Does

PoachGuard analyzes uploaded thermal surveillance videos and detects humans and animals in near real time.

The system:

- enhances thermal frames using CLAHE;
- performs object detection using fine-tuned YOLOv8 models;
- applies separate confidence thresholds for humans and animals;
- highlights humans using red bounding boxes;
- highlights animals using green bounding boxes;
- identifies potential poaching situations when humans and animals occur in the same monitored scene;
- triggers synchronized audio and visual alerts;
- captures evidence frames containing human detections;
- presents detection statistics, timelines, runtime information, and captured frames through a web dashboard.

### 2.2 Problem It Solves

Wildlife poaching remains a critical threat in protected forest regions. Conventional surveillance methods depend heavily on manual patrolling and continuous human monitoring, which are difficult to maintain across large, remote, and low-visibility environments.

Thermal cameras provide visibility based on heat signatures and can assist surveillance during darkness, fog, and difficult lighting conditions. However, raw thermal footage still requires intelligent interpretation to distinguish wildlife movement from unauthorized human intrusion.

PoachGuard addresses this challenge through an automated AI pipeline that transforms thermal video into actionable detection information.

### 2.3 Intended Users

The system is designed as a surveillance and decision-support platform for:

- forest departments;
- wildlife conservation teams;
- national parks and sanctuaries;
- protected-area monitoring units;
- anti-poaching patrol teams;
- researchers working on wildlife surveillance;
- organizations developing AI-assisted conservation systems.

---

## 3. Core Features

### Thermal Video Processing

Thermal surveillance footage is processed frame by frame and prepared for model inference using image enhancement and normalization techniques.

### CLAHE-Based Enhancement

Contrast Limited Adaptive Histogram Equalization enhances local contrast in thermal frames, helping improve the visual separation of heat-emitting subjects from their surroundings.

### Fine-Tuned YOLOv8 Detection

The project uses fine-tuned YOLOv8m and YOLOv8l models configured for domain-relevant human and animal classes.

### Dual Confidence Thresholds

Human and animal detections are evaluated using separate confidence thresholds. This allows stricter validation for potential human intrusions while maintaining sufficient sensitivity for wildlife detection.

### Human–Animal Co-occurrence Analysis

The alert engine evaluates whether humans and animals are present in the monitored scene and uses that information to identify potential poaching-risk events.

### Real-Time MJPEG Streaming

Processed frames are streamed from the backend to the browser through an MJPEG video feed without waiting for the full video to finish.

### Evidence Frame Capture

Frames containing confirmed human detections are preserved and displayed in the captured-frames gallery for review.

### Detection Timeline

Human detection events are recorded chronologically and displayed in a dedicated timeline.

### Alert System

Potential intrusion events trigger synchronized:

- audio alerts;
- visual threat indicators;
- timeline entries;
- captured evidence frames;
- dashboard counter updates.

### Detection Statistics

The dashboard displays:

- humans detected;
- animals detected;
- total alerts;
- application runtime;
- current threat status;
- number of captured evidence frames.

### Evidence Export

Captured frames can be downloaded as a ZIP archive for offline analysis, reporting, or documentation.

### Detection History

Previous processing sessions and detection information can be retained and reviewed through the interface.

### Configurable Settings

Frontend settings and selected preferences are stored locally in the browser for subsequent sessions.

---

## 4. System Interface

<div align="center">

![PoachGuard Dashboard](docs/poachguard-dashboard.png)

</div>

The dashboard is organized into the following functional areas:

| Interface Area | Purpose |
|---|---|
| Upload Video | Selects a thermal surveillance video for analysis |
| Start Detection | Initiates the backend inference pipeline |
| Live Detection Feed | Displays processed video frames with bounding boxes |
| Detection Statistics | Shows humans, animals, alerts, and runtime |
| Human Detection Timeline | Records confirmed human-detection events |
| Captured Frames | Displays evidence images collected during processing |
| Threat Indicator | Shows the current monitoring or alert state |
| Export as ZIP | Downloads captured evidence frames |

> Place the dashboard screenshot inside `docs/poachguard-dashboard.png`, or update the image path above to match its actual location.

---

## 5. Detection Behaviour

| Detection | Bounding Box | System Response |
|---|---|---|
| Human only | Red | Records human detection and captures evidence |
| Animal only | Green | Continues wildlife monitoring |
| Human and animal in the scene | Red and green | Generates a potential poaching alert |
| No relevant object | None | Maintains normal monitoring state |

The system performs object detection and threat interpretation separately. A model detection identifies the objects present, while the event engine determines whether the scene should be treated as a potential threat.

---

## 6. Model Strategy

PoachGuard uses two fine-tuned YOLOv8 variants.

### YOLOv8m

YOLOv8m provides a balanced relationship between inference speed, model size, and detection quality. It is suitable for responsive video processing where hardware resources are limited.

### YOLOv8l

YOLOv8l provides a larger detection architecture for environments where additional computational resources are available and greater feature-extraction capacity is required.

### Fine-Tuning Approach

The models were adapted for the project through:

- thermal dataset preparation;
- annotation conversion into YOLO format;
- domain-specific image augmentation;
- selected human and animal classes;
- thermal contrast enhancement;
- confidence-threshold calibration;
- task-specific fine-tuning through the Ultralytics API.

Restricting the system to relevant object categories reduces unrelated detections and keeps the inference pipeline focused on the intended surveillance task.

> The repository should include measured precision, recall, mAP, and inference-speed results only when they have been obtained from a documented validation run.

---

## 7. Technology Stack

| Layer | Technology | Responsibility |
|---|---|---|
| Programming Language | Python | Core backend and machine-learning pipeline |
| Object Detection | YOLOv8m and YOLOv8l | Human and animal detection |
| Deep-Learning Framework | PyTorch | Model execution and GPU acceleration |
| Computer Vision | OpenCV | Video decoding, enhancement, annotation, and encoding |
| Image Enhancement | CLAHE | Thermal frame contrast improvement |
| Backend Framework | Flask | API routes, upload handling, and application services |
| Video Streaming | MJPEG | Browser-based processed-frame streaming |
| Frontend | HTML5, CSS3, JavaScript | Dashboard and user interaction |
| State Management | Thread-safe Python state layer | Synchronization across inference and UI |
| Browser Storage | Local Storage | Session history and frontend settings |
| Alerting | Browser audio and visual notifications | Intrusion-alert communication |

---

## 8. Core Module Responsibilities

### `engine.py`

`engine.py` is the real-time thermal video inference engine.

Its responsibilities include:

- opening and decoding the thermal video source;
- enhancing frames using CLAHE;
- invoking the fine-tuned YOLOv8 model;
- applying separate confidence thresholds for humans and animals;
- drawing red human and green animal bounding boxes;
- evaluating human–animal co-occurrence;
- generating anti-poaching alert events;
- forwarding processed frames and detection metadata to the application state.

### `train_engine.py`

`train_engine.py` is the YOLOv8 training orchestration pipeline.

Its responsibilities include:

- validating the thermal dataset structure;
- converting source annotations into YOLO-compatible format;
- preparing training and validation splits;
- defining thermal-domain augmentation settings;
- configuring the selected YOLOv8 base model;
- launching model fine-tuning through the Ultralytics API;
- storing training runs, checkpoints, and final weights.

### `state.py`

`state.py` is the thread-safe application state manager.

Its responsibilities include:

- synchronizing the inference engine and Flask routes;
- buffering the latest processed video frame;
- generating the MJPEG stream;
- maintaining detection counters;
- recording human-detection events;
- storing captured evidence frames;
- maintaining the active threat state;
- exposing safe state snapshots to the frontend.

### `app.js`

`app.js` manages the frontend application experience.

Its responsibilities include:

- drag-and-drop video upload;
- file validation;
- starting and stopping detection sessions;
- displaying the live MJPEG feed;
- polling backend status endpoints;
- updating counters and runtime values;
- rendering the human-detection timeline;
- displaying captured evidence frames;
- synchronizing audio and visual alerts;
- exporting evidence frames;
- maintaining history and settings through browser storage.

### `app.py`

`app.py` acts as the web application entry point and API layer.

Its responsibilities include:

- initializing Flask;
- validating required files and configuration;
- loading the inference engine and shared state;
- handling video uploads;
- starting background detection;
- exposing the live stream;
- returning detection status and captured-frame data;
- serving the frontend application.

---

## 9. Application Flow

```text
User opens PoachGuard
        │
        ▼
User uploads a thermal video
        │
        ▼
Backend validates the uploaded file
        │
        ▼
User starts the detection session
        │
        ▼
Video is decoded frame by frame
        │
        ▼
CLAHE enhances thermal-frame contrast
        │
        ▼
Fine-tuned YOLOv8 performs inference
        │
        ├── Human detected ──► Red bounding box
        │
        └── Animal detected ─► Green bounding box
        │
        ▼
Threat decision engine evaluates the scene
        │
        ├── Normal scene ─────► Continue monitoring
        │
        └── Risk condition ───► Trigger poaching alert
                                  │
                                  ├── Play alarm
                                  ├── Update threat status
                                  ├── Record timeline event
                                  └── Capture evidence frame
        │
        ▼
Processed frame is published through MJPEG
        │
        ▼
Dashboard updates statistics and evidence
        │
        ▼
Detection completes and results remain available
```

## 10. System Architecture

PoachGuard follows a layered surveillance architecture built around a Flask backend, a YOLOv8-based detection engine, a thread-safe shared state module, and a browser-based dashboard. The system receives an uploaded surveillance video, processes it frame by frame, detects humans and animals, generates alerts when required, and streams the annotated result to the interface in real time.

---

## 11. Project Structure

```text
animal_poaching_system/
│
├── app.py
├── requirements.txt
├── README.md
├── detector/
│   ├── __init__.py
│   ├── engine.py
│   ├── state.py
│   └── train_engine.py
│
├── models/
│   ├── yolov8m.pt
│   └── yolov8l.pt
│
├── templates/
│   └── index.html
│
├── static/
│   ├── audio/
│   │   └── alarm.mp3
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
│
└── docs/
    └── poachguard-dashboard.png
```

---

## 12. Installation

### Prerequisites

- Python 3.10 or later
- Git
- pip
- NVIDIA GPU with CUDA support for faster inference

### Clone the Repository

```bash
git clone <repository-url>
cd animal_poaching_system
```

### Create a Virtual Environment

#### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

#### Linux or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Add Model Weights

Place the required model files in the `models/` directory.

### Add Alarm Audio

Place the alert sound at:

```text
static/audio/alarm.mp3
```

### Start the Application

```bash
python app.py
```

Open the local address shown in the terminal.

---

## 13. Usage

1. Open the PoachGuard dashboard in a browser.
2. Upload a thermal surveillance video.
3. Start the detection session.
4. Review the live annotated feed.
5. Monitor detection statistics and threat status.
6. Inspect the timeline of human detections.
7. Review captured evidence frames.
8. Export frames as a ZIP archive when required.

---

## 14. Expected Output

The system produces:

* Annotated video frames with bounding boxes
* Human detections highlighted in red
* Animal detections highlighted in green
* Real-time alert status
* Captured evidence frames
* Detection timeline entries
* Runtime statistics
* ZIP export of evidence frames

---

## 15. Training Pipeline

The training pipeline is organized to support thermal-domain model adaptation. It prepares the dataset, converts annotations into YOLO format, defines augmentation settings, fine-tunes the selected YOLOv8 model, and stores the final weights for inference use.

---

## 16. Configuration

Key inference settings are centrally configurable:

```python
MODEL_PATH = "models/yolov8m.pt"
IMAGE_SIZE = 640
HUMAN_CONFIDENCE = 0.45
ANIMAL_CONFIDENCE = 0.35
ENABLE_CLAHE = True
ENABLE_GPU = True
CAPTURE_HUMAN_FRAMES = True
ENABLE_AUDIO_ALERT = True
```

These values should be tuned based on validation results and deployment hardware.

---

## 17. Repository Guidelines

* removed local virtual environments
* excluded cache folders such as `__pycache__`
* avoided committing private or restricted footage
* avoided committing generated outputs unless required
* ensured model weights are legally distributable

Recommended `.gitignore` entries:

```gitignore
__pycache__/
.venv/
env/
venv/
jai/
uploads/*
outputs/*
runs/*
*.zip
*.log
.env
```

---

## 18. Current Scope

The current implementation focuses on:

* thermal-video surveillance analysis
* human and animal detection
* event-based alert generation
* evidence capture
* browser-based monitoring
* dashboard visualization

The system is designed as a decision-support tool for wildlife surveillance.

---

## 19. Limitations

* Performance depends on thermal-video quality
* Dense vegetation can reduce detection accuracy
* Occlusion may hide subjects from the model
* CPU-only execution is significantly slower
* Detection is not equivalent to legal proof of poaching
* Validation on real deployment footage is still necessary

---

## 20. Future Development

Possible future improvements include:

* live CCTV and RTSP support
* multi-camera monitoring
* object tracking across frames
* ranger notification integration
* GPS-enabled incident mapping
* edge deployment
* cloud-based analytics
* automated hotspot analysis

---

## 21. Responsible Use

PoachGuard is intended to support authorized wildlife conservation and surveillance activities. It is designed to detect object categories rather than identify individuals, and should be used with proper legal and operational safeguards.

---

## 22. Contributors

| Name                | Role                      |
| ------------------- | ------------------------- |
| Naveen K            | Model development         |
| HemanthKumar SS     | Backend integration       |
| Jaivarshan V        | Frontend dashboard        |

---

## 23. Acknowledgements

This project uses:

* Ultralytics YOLOv8
* PyTorch
* OpenCV
* Flask
* HTML, CSS, and JavaScript

---
