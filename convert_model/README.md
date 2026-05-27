# คู่มือการ Export โมเดล (YOLOv8/v11 Model Export Guide)

ไฟล์นี้อธิบายรายละเอียดเกี่ยวกับ Arguments (พารามิเตอร์) ต่างๆ ที่ใช้ในกระบวนการแปลงโมเดล (Export) จาก PyTorch (`.pt`) ไปเป็นรูปแบบความเร็วสูง เช่น **ONNX** และ **TensorRT (.engine)** เพื่อนำไปรันบนระบบ Triton Inference Server

---

## 📋 ตารางพารามิเตอร์การ Export (Export Arguments)

| Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **`format`** | `str` | `'engine'` | รูปแบบของโมเดลปลายทางที่ต้องการแปลง เช่น `'onnx'`, `'engine'` (TensorRT), `'openvino'`, `'tflite'` |
| **`imgsz`** | `int` หรือ `tuple` | `640` | ขนาดของภาพ Input ที่ส่งเข้าโมเดล เช่น `640` (640x640) หรือระบุเป็นกว้างxสูง `(height, width)` |
| **`half`** | `bool` | `False` | เปิดใช้งาน FP16 (Half-Precision) ช่วยลดขนาดโมเดลลงครึ่งหนึ่ง และเพิ่มความเร็วบน GPU ที่รองรับ Tensor Core |
| **`int8`** | `bool` | `False` | เปิดใช้งาน INT8 Quantization ช่วยบีบอัดโมเดลให้เล็กลงมากและรันได้เร็วที่สุด (ต้องการไฟล์ข้อมูล Calibrate) |
| **`dynamic`** | `bool` | `False` | เปิดใช้งาน Dynamic Input/Output Shapes ช่วยให้โมเดลรองรับขนาดรูปภาพหรือขนาด Batch Size ที่ยืดหยุ่นได้ |
| **`simplify`** | `bool` | `True` | ทำความสะอาดโครงสร้างกราฟโมเดลด้วย `onnxslim` เพื่อให้โหลดเร็วขึ้นและรองรับการทำงานดีขึ้น |
| **`workspace`** | `float` หรือ `None` | `None` | กำหนดขีดจำกัดหน่วยความจำ GPU (GiB) ที่ตัวแปลง TensorRT จะสามารถเรียกใช้สำหรับการหา Optimization Tactic |
| **`nms`** | `bool` | `False` | ฝัง Core Logic ของ Non-Maximum Suppression (NMS) เข้าไปในตัวโมเดลปลายทางโดยตรง |
| **`batch`** | `int` | `1` | ขนาด Batch Size สูงสุดที่โมเดลหลังแปลงจะรองรับได้ในการประมวลผลพร้อมกัน |
| **`data`** | `str` | `'coco8.yaml'`| พาธของไฟล์ตั้งค่า Dataset (เช่น `.yaml`) สำหรับใช้รันขั้นตอน Calibration ของโมเดลแบบ INT8 |
| **`fraction`** | `float` | `1.0` | อัตราส่วนข้อมูลของ Dataset ที่จะนำมาสุ่มใช้ทำ Calibration สำหรับ INT8 |
| **`device`** | `str` | `None` | ระบุอุปกรณ์ที่จะใช้ในการแปลงโมเดล เช่น `'0'` (GPU ตัวแรก), `'cpu'`, หรือ `'dla:0'` (สำหรับ Jetson) |

---

## 💡 คำอธิบายเชิงลึกและเทคนิคการตั้งค่า

### 1. `half` (FP16) vs `int8` (INT8)
* **FP16 (`half=True`)**: แนะนำมากที่สุดสำหรับการรันบน GPU (เช่น RTX 3060, A100) เนื่องจากให้ความแม่นยำแทบจะเท่าเดิม (ลดลง < 0.1%) แต่ความเร็วเพิ่มขึ้นเกือบ 2 เท่า และใช้ VRAM ลดลงครึ่งหนึ่ง
* **INT8 (`int8=True`)**: เหมาะกับเครื่องปลายทางขนาดเล็ก (Edge Devices) เช่น Nvidia Jetson หรือ CPU แต่ต้องมีขั้นตอน Calibration (ระบุ `--data`) เพื่อป้องกันไม่ให้ความแม่นยำตกมากเกินไป

### 2. `workspace` (ข้อแนะนำสำหรับ GPU แล็ปท็อป/VRAM จำกัด)
* ตัวต่อโมเดล TensorRT จะทดสอบเลือกอัลกอริทึมที่เร็วที่สุดในพื้นที่หน่วยความจำที่เรียกว่า `workspace`
* หากรันบน GPU แล็ปท็อป (เช่น RTX 3060 Laptop 6GB) และมี Triton Server หรือโปรแกรมอื่นรันค้างอยู่ การตั้งค่า `workspace` ไว้สูงเกินไป (เช่น 4GB) จะทำให้เกิดปัญหา **`OutOfMemory (OOM)`** ในตอน compile
* **💡 แนะนำให้ตั้งค่าเป็น `None`** เพื่อให้ TensorRT จัดการจัดสรรหน่วยความจำแบบไดนามิกตามพื้นที่การ์ดจอที่เหลืออยู่ ณ ขณะนั้นโดยอัตโนมัติ หรือปรับลดลงเหลือ `1` หรือ `2` (GB)

### 3. `dynamic` (Dynamic Shapes)
* สำหรับ Triton BLS (Python Router) ที่ร้อยท่อข้อมูลหลายเวอร์ชัน หรือต้องการรองรับการเรียกภาพขนาดไม่เท่ากันในอนาคต **จำเป็นต้องตั้งค่า `dynamic=True`** เพื่อให้โมเดลไม่ผูกมัดตัวเองกับรูปภาพขนาด 640x640 เท่านั้น

---

## 🚀 ตัวอย่างคำสั่งรันแปลงโมเดลยอดนิยม

ก่อนทำการแปลงโมเดล ตรวจสอบให้มั่นใจว่าได้เปิดใช้งาน Conda Environment แล้ว:
```bash
use_conda
conda activate /home/luke/gauge_inspection/.conda
```

#### A. แปลงเป็น ONNX แบบรวดเร็วและใช้ Dynamic Shape (แนะนำสำหรับ Triton เริ่มต้น)
```bash
python3 convert_model/convert_pt.py --model models/analog_gauge_model/segmentation/best_segment_v2.pt --format onnx
```

#### B. แปลงเป็น TensorRT (Engine) โดยการจัดสรรหน่วยความจำอัตโนมัติ (แก้ปัญหา OutOfMemory)
```bash
python3 convert_model/convert_pt.py --model models/analog_gauge_model/segmentation/best_segment_v2.pt --format engine --workspace 1
```

#### C. แปลงโมเดล Analog Gauge ทั้งหมด (v1 และ v2) ไปเป็นทั้งสองฟอร์แมตพร้อมกัน
```bash
python3 convert_model/convert_pt.py --model all --format both --workspace 1
```
