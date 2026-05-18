# 🚀 Super Scale Model Repository Standard (Version 2)

เอกสารฉบับนี้อธิบายโครงสร้างการจัดเก็บโมเดลระดับ Production ที่มีความซับซ้อนสูง รองรับหลายภารกิจ (Task) และมีการใช้โมเดลร่วมกัน (Shared Models) โดยยึดตามมาตรฐานการสแกนของ NVIDIA Triton Server

## 📂 โครงสร้าง Model Repository แบบ "แบนราบ" (Flat Structure)

เพื่อให้ Triton สามารถสแกนและโหลดโมเดลได้โดยอัตโนมัติ เราจะใช้การ **"ตั้งชื่อนำหน้า (Prefix)"** แทนการซ้อนโฟลเดอร์ ดังนี้:

```text
model_repository/
│
├── 🧠 [Orchestrators] - ตัวจัดการลำดับงาน (สูตรอาหาร)
│   ├── task_analog_gauge_router/           
│   │   ├── config.pbtxt               (Version Policy: All)
│   │   ├── 1/ model.py                (V1: สูตรดั้งเดิม)
│   │   ├── 2/ model.py                (V2: สูตรที่ใช้ SR ช่วย)
│   │   └── 3/ model.py                (V3: สูตรใหม่เน้นความเร็ว)
│   │
│   └── task_abnormality_router/            
│       ├── config.pbtxt
│       ├── 1/ model.py                (V1: ตรวจน้ำมันรั่ว)
│       └── 2/ model.py                (V2: ตรวจน้ำมันรั่ว + สนิม)
│
├── 🧱 [Shared Backbones] - โมเดลพื้นฐานที่ใช้ร่วมกันได้
│   ├── shared_yolo_universal/         (โมเดล YOLO ที่ใช้ได้กับหลายงาน)
│   │   ├── config.pbtxt
│   │   ├── 1/ model.onnx              (v1: เก่า)
│   │   └── 2/ model.engine            (v2: TensorRT - แรงกว่า)
│   │
│   ├── shared_swin2sr_optimizer/      (โมเดลขยายภาพ Shared SR)
│   │   ├── config.pbtxt
│   │   └── 1/ model.py
│   │
│   └── shared_doctr_ocr_engine/       (โมเดลอ่านตัวเลข Shared OCR)
│       ├── config.pbtxt
│       ├── 1/ model.py                (V1: CPU)
│       └── 2/ model.py                (V2: GPU Optimized)
│
└── 🛠️ [Utility Models] - โมเดลช่วยประมวลผล
    └── util_math_postprocess/         (สูตรคำนวณคณิตศาสตร์/มุมเข็ม)
        ├── config.pbtxt
        └── 1/ model.py
```

---

## 💡 ทำไมโครงสร้างแบบนี้ถึงดีที่สุดสำหรับ Triton?

### 1. Triton เข้าใจได้ทันที (Auto-Discovery)

Triton จะสแกนหาไฟล์ `config.pbtxt` ในโฟลเดอร์ชั้นแรกเท่านั้น การใช้ชื่อนำหน้า (Prefix) เช่น `task_` หรือ `shared_` ช่วยให้เราจัดกลุ่มด้วยสายตาได้ง่ายในขณะที่ Triton ก็ยังทำงานได้ตามปกติ

### 2. การใช้โมเดลร่วมกันอย่างมีประสิทธิภาพ (Resource Sharing)

เชฟ (Router) ทุกตัวสามารถเรียกใช้ "วัตถุดิบ" ก้อนเดียวกันได้ผ่านคำสั่งภายในโค้ด Python:

```python
# ตัวอย่าง: เรียกใช้ YOLO ตัวท็อปเวอร์ชันล่าสุด
pb_utils.InferenceRequest(model_name="shared_yolo_universal", ...)
```

ช่วยประหยัด GPU Memory เพราะโมเดล Shared จะถูกโหลดขึ้นเครื่องเพียงครั้งเดียว แต่รองรับการเรียกใช้งานจากหลาย Task

### 3. จัดการเวอร์ชันได้อย่างอิสระ (Independent Life-cycle)

* คุณสามารถอัปเกรด `shared_yolo_universal` เป็นเวอร์ชัน 2 ได้โดยไม่ต้องหยุดการทำงานของ Router
* Router สามารถเลือกได้ว่าจะใช้ "วัตถุดิบ" เวอร์ชันเก่าหรือใหม่ผ่านการระบุ `model_version`

### 4. รองรับการขยายตัว (Scalability)

เมื่อมีภารกิจใหม่ (เช่น Task 7: ตรวจวัดระดับน้ำ) คุณเพียงแค่สร้าง `task_water_level_router` ตัวใหม่ขึ้นมา แล้วให้มันไปเรียกโมเดล Shared ที่มีอยู่แล้วมาใช้งานได้ทันทีเหมือนการต่อเลโก้ครับ!
