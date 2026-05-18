# 🛠️ AI Inference Proxy: Payload Lifecycle Management

เอกสารฉบับนี้อธิบายกระบวนการทำงานของ **Inference Proxy** ซึ่งทำหน้าที่เป็นตัวกลางในการแปลงข้อมูล (Data Transformation) ระหว่างหุ่นยนต์/หน้าบ้าน กับ Triton Inference Server ตามมาตรฐาน Version 8 Schema

## 1. วงจรชีวิตของ Payload (Payload Lifecycle)

การไหลของข้อมูลแบ่งออกเป็น 3 ระยะหลัก:

1.  **Payload A (Source Request)**: สร้างโดยหุ่นยนต์หรือสถานีควบคุม (CCR) ประกอบด้วยข้อมูล Metadata ของภารกิจและตำแหน่งอ้างอิงของรูปภาพ
2.  **Payload B (Inference Ready)**: คำขอที่ถูกแปลงเพื่อส่งไปยัง Inference Proxy โดยจะจับคู่ Task ID กับโมเดลที่เกี่ยวข้อง และเตรียมพารามิเตอร์สำหรับนำเข้า
3.  **Payload C (Standardized Result)**: ผลลัพธ์สุดท้ายจาก AI Pipeline ตามมาตรฐาน **Version 8 Schema** ซึ่งจะรวบรวมการทำนายของโมเดลให้อยู่ในรูปแบบ Object ที่มีโครงสร้างชัดเจน

---

## 2. ตรรกะการจับคู่ (Mapping Logic): Payload A → Payload B

สคริปต์ `convert_input.py` จะดำเนินการจับคู่ฟิลด์ดังนี้:

| ฟิลด์ | ต้นทาง (Payload A) | ปลายทาง (Payload B) | หมายเหตุ |
| :--- | :--- | :--- | :--- |
| `inference_request_id` | `inference_request_id` | `inference_request_id` | คงไว้เพื่อการติดตาม (Traceability) |
| `timestamp` | `timestamp` | `timestamp` | รูปแบบ ISO-8601 |
| `inference_task` | `inference_task` | `inference_task` | รหัสตัวเลข (0-5) |
| `image_uri` | `image_uri` | `image_uri` | ที่อยู่รูปภาพ (S3 หรือ local path) |
| `model` | - | *กำหนดจาก Task ID* | เช่น Task 0 -> `gauge_v4` |
| `inference_payload` | `inference_payload` | `inference_payload` | แปลงจาก string เป็น JSON object |

### ตารางการจับคู่โมเดล (Model Mapping)
- `0` (Digital Gauge) -> `gauge_v4`
- `1` (Analog Gauge) -> `gauge_v4`
- `2` (Abnormality) -> `abnormality_v4`
- `3` (Water Level) -> `water_level_v7`
- `4` (Gas Detection) -> `gas_detection_v12`
- `5` (Scanning) -> `scanning_v1`

---

## 3. ตรรกะการจับคู่: Triton Output → Payload C (Version 8)

สคริปต์ `convert_output.py` จะเปลี่ยนผลลัพธ์ดิบจาก AI ให้กลายเป็น "Common Response Schema"

### ส่วนห่อหุ้มส่วนกลาง (Common Envelope)
ทุกผลลัพธ์จะประกอบด้วย:
- `inference_request_id`, `timestamp`, `image_uri`, `inference_task`
- อาเรย์ `results[]` ที่เก็บวัตถุที่ตรวจพบอย่างน้อยหนึ่งรายการ

### กฎการแปลงข้อมูลหลัก (Core Transformation Rules)
- **การจัดการสถานะ (Status Management)**: ข้อผิดพลาดดิบจะถูกแปลงเป็น `inference_status = "FAILED"` พร้อมระบุรายละเอียดใน `inference_error` (code, message, stage)
- **บริบทของวัตถุ (Object Context)**: `object_type` จะถูกทำให้เป็นมาตรฐาน (เช่น `analog_gauge`, `flange`)
- **ผลลัพธ์มาตรฐาน (Standardized Outputs)**: ค่าตัวเลขดิบ (เช่น `value`) จะถูกย้ายเข้าไปใน `outputs` object แบบแบน (เช่น `outputs.gauge_reading`)
- **การดีบั๊ก (Debugging)**: ข้อมูลทางคณิตศาสตร์ (R² score, fit points, needle tips) จะถูกเก็บไว้ในฟิลด์ `debug` เพื่อใช้กับเครื่องมือแสดงผล (Visualization)

### ตัวอย่างการจับคู่ (Analog Gauge)
- Raw `value` -> `outputs.gauge_reading`
- Raw `unit` -> `outputs.unit`
- Raw `r2_score` -> `debug.r2_score`
- Raw `mask` -> `components.gauge_body.mask`

---

## 4. ปรัชญาการออกแบบ (Design Philosophy)
- **Flat Objects**: `outputs` เป็น object แบบแบน ไม่ใช่รายการ key-value เพื่อให้เข้าถึงข้อมูลได้ง่าย เช่น `data.results[0].outputs.gauge_reading`
- **Traceability**: `inference_request_id` จะถูกส่งต่อไปตลอดทั้งกระบวนการ
- **Robustness**: สคริปต์มีการเตรียมตรรกะรองรับ (Fallback logic) เช่น การตั้งสถานะเป็น `FAILED` หากไม่พบข้อมูลที่คาดหวัง เพื่อให้แน่ใจว่าระบบปลายทางจะได้รับข้อมูลตาม Schema ที่ถูกต้องเสมอ
