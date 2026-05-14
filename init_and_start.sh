#!/bin/bash

# ==============================================================================
# Triton Initialization & Startup Script (Fixed Paths)
# ==============================================================================

# 1. กำหนดตำแหน่งที่ทำงาน
BASE_DIR="/home/luke/gauge_inspection"
cd $BASE_DIR

# ------------------------------------------------------------------
# 🚀  [Triton Boot] Exporting CUDA Environment
# ------------------------------------------------------------------
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda/lib64:/usr/lib/x86_64-linux-gnu
export CUDA_VISIBLE_DEVICES=0

echo "------------------------------------------------------------------"
echo "🧪  [System Check] Checking CUDA inside Container..."
python3 -c "import torch; print(f'🔥 PyTorch CUDA Available: {torch.cuda.is_available()}'); print(f'📟 Device Name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
echo "------------------------------------------------------------------"

# ------------------------------------------------------------------
# 🔍  [Triton Boot] Checking for Optimized Models (TensorRT)...
# ------------------------------------------------------------------

# 2. ตรวจสอบโมเดล Segmentation (YOLOv8)
SEG_PT="models/analog_gauge_model/segmentation/best_segment_v2.pt"
SEG_ENGINE="models/analog_gauge_model/segmentation/best_segment_v2.engine"

if [ ! -f "$SEG_ENGINE" ]; then
    echo "⚠️  [Segmentation] Engine not found. Converting $SEG_PT to TensorRT..."
    python3 model_conversion/convert_yolo.py
    if [ $? -eq 0 ]; then
        echo "✅  [Segmentation] Conversion Successful!"
    else
        echo "❌  [Segmentation] Conversion Failed!"
    fi
else
    echo "✅  [Segmentation] TensorRT Engine is ready."
fi

# 3. ตรวจสอบโมเดล OCR (DocTR)
OCR_DIR="models/analog_gauge_model/ocr"
OCR_ONNX="model_conversion/ocr_model.onnx"
OCR_ENGINE="$OCR_DIR/best_model.engine"

if [ ! -f "$OCR_ENGINE" ]; then
    echo "⚠️  [OCR] Engine not found. Starting conversion..."
    if [ ! -f "$OCR_ONNX" ]; then
        python3 model_conversion/convert_ocr.py
    fi
    if [ -f "$OCR_ONNX" ]; then
        # ระบุ Full Path สำหรับ trtexec
        /usr/src/tensorrt/bin/trtexec --onnx=$OCR_ONNX --saveEngine=$OCR_ENGINE --fp16 --skipInference
    fi
else
    echo "✅  [OCR] TensorRT Engine is ready."
fi

echo "------------------------------------------------------------------"
echo "🚀  [Triton Boot] Starting Inference Server..."
echo "------------------------------------------------------------------"

# 4. รัน Triton Server (ระบุ Full Path เพื่อความชัวร์)
/opt/tritonserver/bin/tritonserver \
    --model-repository=$BASE_DIR/triton_project/model_repository \
    --log-verbose=1 \
    --strict-model-config=false
