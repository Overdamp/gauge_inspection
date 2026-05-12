FROM nvcr.io/nvidia/tritonserver:26.04-py3

# ติดตั้ง System Dependencies สำหรับ OpenCV (Ubuntu 24.04)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Reinstall numpy to fix version detection bug with transformers in Python 3.12
RUN pip uninstall -y numpy && pip install "numpy>=1.24,<2.0"

# ติดตั้ง Python Packages ที่จำเป็นสำหรับ BLS Pipeline
RUN pip install \
    ultralytics \
    scikit-image \
    python-doctr \
    "transformers>=4.30" \
    timm

# เคลียร์ OpenCV ตัวเต็มออกเพื่อป้องกันปัญหาจอภาพ (Headless)
RUN pip uninstall -y opencv-python opencv-python-headless && \
    pip install opencv-python-headless
