# Analog Gauge Inspector (Triton Task)

เอกสารนี้อธิบายการทำงานของโมเดล `analog_gauge_inspector` ซึ่งเป็น Task ที่ถูกแปลงมาจากสคริปต์ `visualize.py` เพื่อให้นำไปรันบนระบบ **NVIDIA Triton Inference Server** ในรูปแบบของ **Python Backend**

## 📌 จุดประสงค์ของ Task นี้
ทำหน้าที่รับภาพหน้าปัดเกจ (Analog Gauge) เข้ามาประมวลผลด้วยโมเดล Segmentation (YOLOv8) จากนั้นวาดเส้นกรอบ (Contours) และกล่องข้อความ (Bounding Boxes + Confidence) ทับลงบนภาพ และคืนค่ากลับไปทั้ง **ภาพที่วาดเสร็จแล้ว** และ **ข้อมูลดิบในรูปแบบ JSON**

---

## 📂 โครงสร้างไฟล์
ไฟล์ทั้งหมดของ Task นี้เก็บอยู่ที่: `triton_project/task/analog_gauge_inspector/`
```text
analog_gauge_inspector/
├── 1/
│   └── model.py         # โค้ด Python ที่ประมวลผล (Orchestrator/Backend)
└── config.pbtxt         # ไฟล์ตั้งค่าสำหรับ Triton
```

---

## ⚙️ ข้อมูล Input / Output

อ้างอิงจากไฟล์ `config.pbtxt` โมเดลตัวนี้มีโครงสร้างการเชื่อมต่อดังนี้:

### **Input**
*   **ชื่อ:** `IMAGE`
*   **Data Type:** `TYPE_UINT8`
*   **Shape:** `[-1, -1, 3]` *(รองรับภาพสี RGB แบบ Dynamic Size)*

### **Output**
โมเดลนี้คืนค่ากลับมา 2 อย่าง (เพื่อความยืดหยุ่นในการนำไปใช้ต่อ):
1.  **ชื่อ:** `VISUALIZED_IMAGE`
    *   **Data Type:** `TYPE_UINT8`
    *   **Shape:** `[-1, -1, 3]`
    *   **คำอธิบาย:** รูปภาพที่มีการวาด Contours พื้นที่ของหน้าปัด และเขียน Text บอกชื่อคลาสและค่าความมั่นใจ (Confidence) เรียบร้อยแล้ว (เหมาะสำหรับแสดงผลให้ User ดู)
2.  **ชื่อ:** `SEGMENTATIONS_JSON`
    *   **Data Type:** `TYPE_STRING`
    *   **Shape:** `[1]`
    *   **คำอธิบาย:** ข้อมูลผลลัพธ์ในรูปแบบ JSON String ซึ่งประกอบด้วย `class`, `confidence` และพิกัด `mask_points` ทั้งหมด (เหมาะสำหรับนำไปคำนวณต่อในระบบอื่น)

---

## 💻 การทำงานภายใน (`model.py`)
โค้ดใน `model.py` จะถูกเรียกทำงานโดย Triton แบ่งเป็น 3 ส่วนหลัก:
1. **`initialize()`**: 
   จะถูกเรียก **ครั้งเดียว** ตอนสตาร์ท Triton เซิร์ฟเวอร์ ทำหน้าที่โหลด `config.yaml` และโหลดโมเดลน้ำหนัก (Weights `best_segment_v2.pt`) ลงบน GPU ผ่านคลาส `GaugeSegmentor`
2. **`execute()`**: 
   จะถูกเรียก **ทุกครั้ง** ที่มี Request เข้ามา ทำหน้าที่รับภาพ -> สั่งหา Segmentation -> วาดภาพด้วย `cv2.drawContours` -> จัดเตรียมข้อมูล JSON -> สร้าง Output Tensors ส่งคืนให้ Client
3. **`finalize()`**: 
   ใช้สำหรับเคลียร์หน่วยความจำตอนปิดเซิร์ฟเวอร์

---

## 🚀 วิธีการทดสอบ / นำไปใช้งาน
เพื่อนำโมเดลนี้ไปใช้งานบน Triton:
1. ให้คัดลอกโฟลเดอร์ `analog_gauge_inspector` ไปวางไว้ในโฟลเดอร์ `model_repository/` ของคุณ
2. สตาร์ท Triton Server โดยอ้างอิง path ของ `model_repository` นั้น
3. ฝั่งหน้าบ้าน (Client) เพียงแค่อ่านไฟล์รูปเป็น Numpy Array (`cv2.imread`) และส่งยิง API มาหาชื่อโมเดล `analog_gauge_inspector` ได้เลย
