# 🚀 Analog Gauge Inspection - Command Cheatsheet

ไฟล์รวมคำสั่ง Command Line ที่จำเป็นสำหรับการใช้งานโปรเจคนี้ (Triton Inference Server)

---

## 🐳 Docker (Triton Server)

### 1. เริ่มต้นใช้งาน (Start Server)
รันคำสั่งนี้เพื่อเปิดใช้งาน Triton Server พร้อม GPU และ Shared Memory 8GB:
```bash
docker run -d \
  --gpus all \
  --shm-size=8g \
  -p 8000:8000 -p 8001:8001 -p 8002:8002 \
  -v /home/luke/gauge_inspection:/home/luke/gauge_inspection \
  --name triton_bls \
  custom_tritonserver:latest \
  tritonserver \
    --model-repository=/home/luke/gauge_inspection/triton_project/model_repository \
    --log-verbose=1 \
    --strict-model-config=false
```

### 2. จัดการ Container
*   **ดูสถานะ:** `docker ps`
*   **ดู Log การทำงาน:** `docker logs -f triton_bls`
*   **หยุดการทำงาน:** `docker stop triton_bls`
*   **เริ่มทำงานใหม่ (Restart):** `docker restart triton_bls`
*   **ลบ Container:** `docker rm triton_bls`
*   **ลบ Container (บังคับหยุดทันที):** `docker rm -f triton_bls`

---

## 🐍 Python Client (Testing)

### 1. ทดสอบแบบปกติ (Batch Process)
รันทุกรูปในโฟลเดอร์ `images/analog-gauge` (ใช้โมเดลล่าสุด):
```bash
python triton_project/test_client.py
```

### 2. ทดสอบแบบแยกเวอร์ชัน (v1 vs v2)
ใช้เปรียบเทียบระหว่างแบบ **Squish (v1)** และ **Letterbox (v2)**:
*   **เทส Version 1:** `python triton_project/test_client_multi.py 1`
*   **เทส Version 2:** `python triton_project/test_client_multi.py 2`

### 3. รันโปรแกรมต้นฉบับ (Legacy Pipeline)
```bash
python main.py
```

---

## 🌐 Triton API (Manual Check)

### 1. เช็คความพร้อมของ Server
```bash
curl -s localhost:8000/v2/health/ready
```

### 2. ดูสถานะโมเดลที่โหลดอยู่ (Model Repository Index)
```bash
curl -X POST -s localhost:8000/v2/repository/index | json_pp
```

---

## 📁 โฟลเดอร์ผลลัพธ์ (Results)
*   **Triton v1:** `results/triton_results_v1/`
*   **Triton v2:** `results/triton_results_v2/`
*   **Main.py:** `results/` และ `debug_output/`

---

## 🛠 Common Issues

### 1. Error: Conflict. The container name "/triton_bls" is already in use.
หากเจอปัญหานี้ แปลว่ามี Container ชื่อนี้รันอยู่แล้ว ให้เลือกทำอย่างใดอย่างหนึ่ง:
*   **ถ้าต้องการรันใหม่ทั้งหมด:** รัน `docker rm -f triton_bls` ก่อนแล้วค่อยรันคำสั่ง Start Server
*   **ถ้าต้องการแค่เริ่มระบบใหม่:** รัน `docker restart triton_bls`
