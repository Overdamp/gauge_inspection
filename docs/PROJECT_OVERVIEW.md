# Analog Gauge Inspection Project - Project Overview

## 🎯 Project Summary

This is an **Analog Gauge Automatic Reading System** that uses Computer Vision and Deep Learning to automatically detect and read values from analog gauges in images. The system processes cropped gauge images and extracts numerical readings using advanced techniques like image segmentation, OCR (Optical Character Recognition), and geometric fitting.

---

## 📋 Project Objectives

1. **Automatic Gauge Detection**: Identify gauge components in cropped images
2. **Segmentation**: Segment gauge parts (dial, needle, scale text)
3. **OCR Processing**: Extract numerical values and units from gauge scales
4. **Ellipse Fitting**: Fit ellipse models to gauge dials
5. **Needle Detection**: Identify and extract needle position
6. **Value Calculation**: Calculate gauge readings based on needle angle and calibration
7. **Debugging & Visualization**: Generate detailed debug reports for quality assurance

---

## 📁 Project Structure

```
gauge_inspection/
├── main.py                          # Entry point - Batch inference pipeline
├── visualize.py                     # Standalone visualization module
├── configs/
│   └── config.yaml                  # Configuration file (YAML format)
├── cores/                           # Core utilities and helpers
│   ├── __init__.py
│   ├── config_loader.py            # YAML config loader
│   ├── logger.py                    # Logging setup
│   └── visualizer.py               # Visualization utilities
├── libs/
│   └── analog_gauge/               # Main ML/CV library
│       ├── __init__.py
│       ├── detection.py            # YOLO-based gauge detection
│       ├── segmentation.py         # Gauge component segmentation
│       ├── ellipsefit.py           # Ellipse fitting algorithm
│       ├── gauge_cal.py            # Calibration & value calculation
│       ├── gauge_debug.py          # Debug report generation
│       ├── ocr_ai.py               # OCR (Doctr-based)
│       ├── superresolution.py      # Super-resolution enhancement
│       └── visualizer.py           # Visualization helpers
├── tasks/
│   └── analog_gauge_task.py        # Task orchestration class
├── models/                          # Pre-trained model files
│   └── analog_gauge_model/
│       ├── ocr/                    # OCR model weights
│       │   ├── best_model.pt
│       │   └── config.json
│       └── segmentation/           # Segmentation models (multiple versions)
│           ├── best_seg_analog_1.engine
│           ├── best_seg_analog_1.onnx
│           ├── best_seg_analog_1.pt
│           ├── best_segment_v1.*
│           ├── best_segment_v2.pt (currently used)
│           └── ...
├── logs/                            # Log output files
├── runs/                            # YOLO inference outputs
│   └── segment/predict*/           # Prediction results
├── debug_output/                    # Generated debug reports
├── LICENSE
└── README.md                        # Documentation (if exists)
```

---

## 🔄 Workflow & Pipeline

### **Main Execution Flow** (`main.py`)

```
Load Config
    ↓
Setup Logger
    ↓
Initialize AnalogGaugeTask (Load all models)
    ↓
For each image in input folder:
    ├─ Load image with OpenCV
    ├─ Execute analog_task.execute()
    ├─ Get gauge reading (value, unit, R² score)
    ├─ Save debug image (if enabled)
    └─ Log results
    ↓
Output results to output folder
Report total success rate and processing time
```

### **Task Execution Flow** (`AnalogGaugeTask.execute()`)

```
Input: Cropped gauge image
    ↓
1. Segmentation: Detect gauge components
   └─ Output: Segmentation masks for classes (dial, needle, scale, etc.)
    ↓
2. Ellipse Fitting: Fit ellipse to gauge dial
   └─ Output: Center point, ellipse parameters
    ↓
3. OCR Processing: Extract numerical scale values
   └─ Output: Detected numbers and their positions
    ↓
4. Needle Detection: Identify actual needle in image
   └─ Output: Needle mask, needle angle
    ↓
5. Calibration & Calculation:
   ├─ Map needle angle to gauge value
   ├─ Calculate R² score (quality metric)
   └─ Output: Final reading value + unit
    ↓
6. Debug Report: Generate visualization panel
   └─ Output: 8-panel debug image (if debug enabled)
    ↓
Output: {value, unit, r2_score, debug_img, ...}
```

---

## 🤖 Key Components

### **1. Segmentation Module** (`segmentation.py`)
- **Model**: YOLOv8 (PyTorch format)
- **Purpose**: Segment gauge components
- **Input**: Cropped gauge image
- **Output**: Class masks (dial, needle, scale text, etc.)
- **Config**: `analog_gauge.segmentation` in `config.yaml`

### **2. Ellipse Fitter** (`ellipsefit.py`)
- **Purpose**: Fit an ellipse model to the circular/elliptical gauge dial
- **Input**: Gauge dial mask
- **Output**: Center point (cx, cy), ellipse parameters (a, b, angle)
- **Usage**: Normalizes coordinate system for angle calculation

### **3. OCR Module** (`ocr_ai.py`)
- **Model**: Doctr-based OCR
- **Purpose**: Extract numerical text from gauge scale
- **Input**: Scale region crops
- **Output**: Detected text strings and their bounding boxes
- **Device**: CPU or CUDA (configurable)

### **4. Gauge Calculator** (`gauge_cal.py`)
- **Purpose**: Convert needle angle to actual gauge value
- **Process**:
  1. Determine needle angle relative to dial center
  2. Map angle to corresponding gauge value
  3. Calculate linear fit (R² score) for confidence
- **Output**: Reading value, unit, R² score

### **5. Super-Resolution** (`superresolution.py`)
- **Model**: Swin2SR (default: lightweight x2)
- **Purpose**: Enhance image quality before processing
- **Optional**: Used to improve segmentation accuracy

### **6. Debug Generator** (`gauge_debug.py`)
- **Purpose**: Create 8-panel visualization report
- **Panels**:
  1. Original Input
  2. Segmentation Overlay
  3. Ellipse Fitting
  4. OCR Crops + Text
  5. Needle Selection (anti-shadow scoring)
  6. Calibration Plot
  7. Radius Analysis
  8. Final Result with Status

---

## ⚙️ Configuration (`config.yaml`)

```yaml
system:
  log_level: "INFO"
  log_file: "logs/analog_system.log"

analog_gauge:
  device: "cuda"              # GPU acceleration
  ocr_model_dir: "models/analog_gauge_model/ocr"
  segmentation:
    model_path: "models/analog_gauge_model/segmentation/best_segment_v2.pt"
    conf: 0.5                 # Confidence threshold
    iou: 0.5                  # IoU threshold
    verbose: False
  superresolution:
    model_name: "caidas/swin2SR-lightweight-x2-64"
  debug:
    enabled: true
    output_dir: "debug_output"
```

---

## 📊 Input/Output Format

### **Input**
- **Location**: `/home/engineer00/winworkspace/PTTEP/Objectdetection/crop_gauge_result/analog-gauge`
- **Format**: JPG, JPEG, PNG, BMP
- **Content**: Pre-cropped gauge images (focused on single gauge)

### **Output**
- **Location**: `/home/engineer00/winworkspace/PTTEP/AnalogGaugeReading/gauge-win-v3/results`
- **Files**: 
  - `result_{filename}`: Debug image (on success)
  - `failed_{filename}`: Debug image (on failure)
  - Console logs showing extracted values

### **Result Dictionary**
```python
{
    "value": 45.5,           # Extracted gauge reading
    "unit": "PSI",           # Unit of measurement
    "r2_score": 0.95,        # Quality/confidence score (0-1)
    "debug_img": ndarray,    # 8-panel visualization
    "needle_angle": 125.3,   # Needle angle (degrees)
    "center": (240, 300),    # Gauge center coordinates
    ...                      # Additional debug info
}
```

---

## 🔧 Dependencies & Models

### **Python Libraries**
- `ultralytics` - YOLO detection/segmentation
- `opencv-python (cv2)` - Image processing
- `numpy` - Numerical computing
- `torch` - PyTorch framework
- `doctr` - OCR engine
- `pyyaml` - Configuration parsing
- `huggingface_hub` - Model downloading

### **Pre-trained Models**
- **Segmentation**: YOLOv8 (best_segment_v2.pt)
- **OCR**: Doctr model (loaded from `ocr_model_dir`)
- **Super-Resolution**: Swin2SR (HuggingFace hub)

---

## 📈 Key Features

✅ **Batch Processing**: Process multiple images efficiently
✅ **GPU Acceleration**: CUDA support for faster inference
✅ **Debug Mode**: 8-panel visualization for quality assurance
✅ **Logging**: Comprehensive logging to file and console
✅ **Error Handling**: Graceful handling of failed detections
✅ **Confidence Metrics**: R² score for reading quality
✅ **Concurrent Processing**: Optional multi-threading support
✅ **Flexible Configuration**: YAML-based configuration

---

## 🚀 Usage

### **Run Batch Inference**
```bash
python main.py
```

### **Visualize Segmentation Results**
```bash
python visualize.py
```

---

## 📝 Logs & Debugging

- **Log File**: `logs/analog_system.log`
- **Debug Reports**: `debug_output/debug_{filename}.jpg` (8-panel)
- **Console Output**: Shows real-time processing status with success/failure counts

---

## 🎓 Technical Notes

1. **Needle Angle Calculation**: 
   - Uses anti-shadow scoring to identify true needle
   - Calculates angle relative to ellipse center
   - Maps angle to gauge scale values

2. **Calibration**:
   - Linear mapping: angle → value
   - R² score indicates goodness of fit
   - Dual-scale detection for complex gauges

3. **Segmentation Masks**:
   - Color-coded visualization (different class = different color)
   - Used for ellipse fitting and needle detection
   - Multiple model versions available (v1, v2, etc.)

4. **OCR Processing**:
   - Extracts scale text (0, 10, 20, 30, etc.)
   - Uses text positions to calibrate angle-to-value mapping
   - Handles various gauge scales and units

---

## 📞 File Descriptions

| File | Purpose |
|------|---------|
| `main.py` | Main entry point for batch inference |
| `visualize.py` | Standalone segmentation visualization |
| `config_loader.py` | YAML configuration loader |
| `logger.py` | Logging setup and utilities |
| `detection.py` | YOLO-based detection class |
| `segmentation.py` | Gauge component segmentation |
| `ellipsefit.py` | Ellipse fitting algorithm |
| `gauge_cal.py` | Calibration and value calculation |
| `ocr_ai.py` | OCR engine (Doctr) |
| `superresolution.py` | Super-resolution enhancement |
| `gauge_debug.py` | Debug report generation |
| `analog_gauge_task.py` | Main task orchestrator |

---

## 🎯 Project Status

- ✅ Segmentation models trained and ready
- ✅ OCR and calibration logic implemented
- ✅ Debug visualization fully functional
- ✅ Batch processing pipeline operational
- ✅ GPU acceleration configured

**Last Updated**: May 2026
