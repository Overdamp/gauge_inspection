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

มาดูคำอธิบายแต่ละส่วนของคำสั่งกันครับ:

docker run: สั่งให้รัน container ใหม่

-d: รันในโหมด Detached (ทำงานอยู่เบื้องหลัง ไม่ค้างอยู่ที่ Terminal)

--gpus all: อนุญาตให้ Container เข้าถึงและใช้งาน GPU ทุกตัวในเครื่องได้ (สำคัญมากสำหรับการประมวลผล AI)

--shm-size=8g: กำหนดขนาดของ Shared Memory (ใน /dev/shm) ให้เป็น 8GB (ช่วยให้การรับส่งข้อมูลขนาดใหญ่ระหว่างโมเดล หรือ Python Backend ทำได้เร็วขึ้นและไม่แครช)

-p 8000:8000 -p 8001:8001 -p 8002:8002: Map พอร์ตจาก Container ออกมาที่เครื่อง Host เพื่อให้เราเรียกใช้งานได้

8000: สำหรับการเชื่อมต่อแบบ HTTP/REST

8001: สำหรับการเชื่อมต่อแบบ gRPC (เร็วกว่า HTTP เหมาะสำหรับงานโปรดักชัน)

8002: สำหรับดึงข้อมูล Metrics ของเซิร์ฟเวอร์ (เช่น การใช้ GPU, จำนวน Request)

-v /home/luke/gauge_inspection:/home/luke/gauge_inspection: ทำการ Mount (เชื่อมต่อ) โฟลเดอร์ gauge_inspection จากเครื่อง Host เข้าไปไว้ใน Container ที่ Path เดียวกัน เพื่อให้ Triton มองเห็นไฟล์และโมเดลที่อยู่ในนั้น

--name triton_bls: ตั้งชื่อ Container นี้ว่า triton_bls เพื่อให้จำง่ายเวลาต้องการสั่ง stop/start หรือดู log

custom_tritonserver:latest: ระบุชื่อ Image ที่จะนำมารัน ซึ่งในที่นี้คือ Image ที่คุณน่าจะสร้างขึ้นมาเองชื่อ custom_tritonserver เวอร์ชัน latest

tritonserver: คือคำสั่งหลักที่ส่งเข้าไปให้ Container เริ่มทำงาน (ปลุก Triton Server)

--model-repository=/home/luke/gauge_inspection/triton_project/model_repository: บอก Triton ว่าโฟลเดอร์ที่เก็บโมเดล AI ต่างๆ (เช่น gauge_v4, abnormality_v4) อยู่ที่ไหน

--log-verbose=1: สั่งให้ Triton แสดง Log ละเอียดขึ้นระดับ 1 (มีประโยชน์ตอน Debug)

--strict-model-config=false: ปิดโหมด Strict Configuration (อนุญาตให้ Triton โหลดโมเดลขึ้นมาได้ แม้ว่าจะไม่ได้เขียนไฟล์ config.pbtxt ไว้ครบถ้วนสมบูรณ์ โดยมันจะพยายามเดาการตั้งค่าให้เอง)

### 2. จัดการ Container

* **ดูสถานะ:** `docker ps`
* **ดู Log การทำงาน:** `docker logs -f triton_bls`
* **หยุดการทำงาน:** `docker stop triton_bls`
* **เริ่มทำงานใหม่ (Restart):** `docker restart triton_bls`
* **ลบ Container:** `docker rm triton_bls`
* **ลบ Container (บังคับหยุดทันที):** `docker rm -f triton_bls`
* **ดูสถานะและรายละเอียดเพิ่มเติม:** `docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.CreatedAt}}"`
* **ดูประวัติคำสั่ง:** `history | grep "docker"`

# ดู Log ของ docker service ตั้งแต่เมื่อวานจนถึงวันนี้

sudo journalctl -u docker.service --since yesterday --until today

## 🐍 Python Client (Testing)

### 1. ทดสอบแบบปกติ (Batch Process)

รันทุกรูปในโฟลเดอร์ `images/analog-gauge` (ใช้โมเดลล่าสุด):

```bash
python triton_project/test_client.py
```

### 2. ทดสอบแบบแยกเวอร์ชัน (v1 vs v2)

ใช้เปรียบเทียบระหว่างแบบ **Squish (v1)** และ **Letterbox (v2)**:

* **เทส Version 1:** `python triton_project/test_client_multi.py 1`
* **เทส Version 2:** `python triton_project/test_client_multi.py 2`

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

* **Triton v1:** `results/triton_results_v1/`
* **Triton v2:** `results/triton_results_v2/`
* **Main.py:** `results/` และ `debug_output/`

---

## 🛠 Common Issues

### 1. Error: Conflict. The container name "/triton_bls" is already in use

หากเจอปัญหานี้ แปลว่ามี Container ชื่อนี้รันอยู่แล้ว ให้เลือกทำอย่างใดอย่างหนึ่ง:

* **ถ้าต้องการรันใหม่ทั้งหมด:** รัน `docker rm -f triton_bls` ก่อนแล้วค่อยรันคำสั่ง Start Server
* **ถ้าต้องการแค่เริ่มระบบใหม่:** รัน `docker restart triton_bls`

---

## 📦 Inference Proxy

### 1. ทดสอบการแปลง Input (Payload A ⮕ B)

ใช้สำหรับตรวจสอบการจับคู่ Task ID กับ Model และการ Parse JSON พารามิเตอร์:

```bash
python inference_proxy/convert_input.py
```

### 2. ทดสอบการแปลง Output (Triton ⮕ Payload C v8)

ใช้สำหรับตรวจสอบการจัดโครงสร้างผลลัพธ์ให้เป็นมาตรฐาน Version 8 (Flat Outputs):

```bash
python inference_proxy/convert_output.py
```

### 3. ตรวจสอบรายละเอียดกระบวนการ

อ่านคำอธิบายขั้นตอนการทำงานและ Logic การจับคู่ฟิลด์ทั้งหมดได้ที่:
`inference_proxy/process_explanation.md`

### 4. ทดสอบระบบรวมกับ Triton (Integrated End-to-End)

ใช้สำหรับทดสอบตั้งแต่รับ Payload A ไปจนถึงได้ Payload C v8 จาก Server จริง:

```bash
python inference_proxy/triton_integrated_client.py
```

*(หมายเหตุ: ต้องรัน Triton Server ไว้ก่อนถึงจะใช้งานคำสั่งนี้ได้)*
