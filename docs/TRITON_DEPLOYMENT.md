# ข้อมูลเตรียมการสำหรับ NVIDIA Triton Inference Server

เอกสารนี้รวบรวมข้อมูลโครงสร้าง Input และ Output ของแต่ละโมเดลที่ใช้ในระบบ Analog Gauge Inspection เพื่อนำไปใช้สำหรับเขียนไฟล์ `config.pbtxt` ในการจัดการโมเดลบน NVIDIA Triton

---

## 1. โมเดล Segmentation (YOLOv8-seg)
ไฟล์ต้นฉบับ: `best_segment_v2.pt` 
(หมายเหตุ: แนะนำให้ Export เป็น ONNX หรือ TensorRT ก่อนนำขึ้น Triton)

*   **Input**:
    *   **ชื่อ:** `images` (อาจแตกต่างกันขึ้นอยู่กับการ Export)
    *   **Data Type:** `TYPE_FP32` (หรือ `TYPE_FP16` ถ้าทำ quantization)
    *   **Shape:** `[-1, 3, 640, 640]` *(Batch, Channel, Height, Width)*
*   **Output** (สำหรับ YOLOv8-seg มักจะออกเป็น 2 หัว):
    *   **ชื่อ 1 (Bbox + Mask Coefficients):** `output0`
        *   **Shape:** `[-1, N, 8400]` *(N = 4 (พิกัด) + จำนวนคลาส + 32 (Mask coeffs))*
    *   **ชื่อ 2 (Mask Prototypes):** `output1`
        *   **Shape:** `[-1, 32, 160, 160]`

---

## 2. โมเดล Super Resolution (Swin2SR)
โมเดล: `caidas/swin2SR-lightweight-x2-64` (จาก HuggingFace Transformers)

*   **Input**:
    *   **ชื่อ:** `pixel_values`
    *   **Data Type:** `TYPE_FP32`
    *   **Shape:** `[-1, 3, -1, -1]` *(รองรับ Dynamic Height และ Width ตามขนาดของกรอบภาพที่ตัดมา)*
*   **Output**:
    *   **ชื่อ:** `logits` หรือ `reconstruction`
    *   **Shape:** `[-1, 3, -1, -1]` *(ผลลัพธ์จะเป็นภาพที่มีขนาด (Height, Width) ใหญ่ขึ้น 2 เท่าจาก Input (x2))*

---

## 3. โมเดล OCR (python-doctr)
ไลบรารี `doctr` ภายในจะทำงานโดยแบ่งเป็น 2 โมเดลย่อยแยกกัน หากจะจัดการด้วย Triton ต้องแยก Deployment เป็น 2 โมเดลดังนี้:

### 3.1 Text Detection (เช่น DBNet / FAST)
*   **Input**:
    *   **ชื่อ:** `x` หรือ `input`
    *   **Shape:** `[-1, 3, -1, -1]` *(มักจะ fix ความละเอียดเป็น 1024x1024 หรือเป็น Dynamic ก็ได้)*
    *   **Data Type:** `TYPE_FP32`
*   **Output**:
    *   **ชื่อ:** `preds` หรือ `proba_map` (ค่าความน่าจะเป็นของบริเวณที่เป็นตัวอักษร)
    *   **Shape:** `[-1, 1, -1, -1]`

### 3.2 Text Recognition (เช่น CRNN / MASTER)
*   **Input**:
    *   **ชื่อ:** `x` หรือ `input`
    *   **Shape:** `[-1, 3, 32, 128]` *(รับภาพตีกรอบของตัวอักษร โดยทั่วไปปรับความสูง 32 ความกว้าง 128)*
    *   **Data Type:** `TYPE_FP32`
*   **Output**:
    *   **ชื่อ:** `logits`
    *   **Shape:** `[-1, W, C]` *(W = ความยาวของ Sequence, C = จำนวนตัวอักษรที่เป็นไปได้ในพจนานุกรมของโมเดล)*

---

## 💡 ข้อแนะนำเพิ่มเติมสำหรับการทำ Triton Deployment
1. **Dynamic Batching:** แนะนำให้ตั้งค่ามิติแรก (Batch Size) ของทุกโมเดลใน `config.pbtxt` เป็น `-1` (Dynamic) เพื่อให้ Triton สามารถรวบรวม Request หลายๆ อันมารันพร้อมกันได้เต็มประสิทธิภาพ โดยเฉพาะโมเดล **Text Recognition** และ **Super Resolution** ที่ระบบปัจจุบันมีการส่งภาพเข้าไปทำงานแบบ Batch อยู่แล้ว
2. **Model Conversion:** ก่อนจะนำไปใช้งาน ควรแปลงโมเดล PyTorch (`.pt`, `.bin`) ให้อยู่ในฟอร์แมต **ONNX (`.onnx`)** หรือ **TensorRT (`.engine` / `.plan`)** เพื่อความรวดเร็วในการทำงานบน GPU (สำหรับ YOLOv8 ใช้คำสั่ง `yolo export model=best_segment_v2.pt format=onnx dynamic=True` ได้เลย)

---

## 🛠 แผนการสร้างสถาปัตยกรรมแบบ Multi-Task (Triton Python Backend)

เนื่องจากระบบมีแผนจะรองรับหลายงาน (Analog Gauge, Digital Gauge, Flange, Lever Valve ฯลฯ) สถาปัตยกรรมที่แนะนำที่สุดบน Triton คือ **Business Logic Scripting (BLS) / Python Backend** โดยสร้างโมเดลตัวแปรกลาง (Orchestrator) เพื่อควบคุม Flow ของข้อมูลดังนี้:

### โครงสร้างการทำงานของ "Master Router" (Orchestrator)
ฝั่ง Client จะส่งเพียงรูปภาพและระบุประเภทงาน (`task_type`) จากนั้น Python Backend ใน Triton จะเป็นตัวตรวจสอบเงื่อนไขและเลือกโมเดลที่เหมาะสม

```python
# ตัวอย่างคอนเซปต์ Python Backend (BLS) ภายใน Triton
task_type = request.parameters["task_type"]

if task_type == "analog_gauge":
    # 1. รันโมเดล Segmentation (YOLOv8)
    # 2. ตัดรูปภาพ (Image Crop)
    # 3. รัน Super Resolution และ OCR
    # 4. คืนค่าตัวเลขและองศา

elif task_type == "digital_gauge":
    # 1. รัน Object Detection หาหน้าจอ
    # 2. รัน OCR แบบเฉพาะเจาะจง

elif task_type == "flange_inspection":
    # 1. รัน Anomaly Detection
    # 2. คืนผลตรวจสนิม / การรั่วไหล

else:
    return "Unknown task"
```

**ข้อดีของการใช้สถาปัตยกรรม BLS:**
*   **Single Endpoint:** ฝั่งหน้าบ้าน (Client) เรียก API เพียงช่องทางเดียว ไม่ต้องส่งรูปไป-กลับหลายรอบ
*   **Dynamic Flow:** สามารถแชร์โมเดลร่วมกันได้ เช่น งาน A และ งาน B สามารถเรียกใช้ OCR ตัวเดียวกันใน Triton ได้ทันที (ลดการใช้ VRAM)
*   **Scalable:** หากในอนาคตมี Inspection แบบใหม่เข้ามา ก็เพียงแค่อัปโหลดโมเดลใหม่ขึ้น Triton และเพิ่มเงื่อนไข `elif` ในไฟล์ Orchestrator โดยไม่กระทบกับระบบที่กำลังทำงานอยู่

---

## 🚀 สถาปัตยกรรมแบบผสมผสาน (Hybrid Architecture) สำหรับ Wide Scene Inspection

ในสถานการณ์จริงที่หุ่นยนต์ส่ง **ภาพกว้าง (Wide Scene)** 1 ภาพ ซึ่งอาจมีทั้ง Analog Gauge, Flange และ Lever Valve รวมอยู่ในภาพเดียว การออกแบบที่ทรงประสิทธิภาพที่สุดคือการใช้ **"Python Backend (BLS) + Multiple Instances"** ร่วมกับโครงสร้างแบบ **2-Stage Pipeline (ค้นหา -> เจาะจง)**

### การตั้งค่าและโครงสร้างการทำงาน
1. **Global Spotter (YOLOv8 Detection):**
   *   ใช้โมเดล Object Detection ตัวแม่ ทำหน้าที่ค้นหาตำแหน่ง (Bbox) และแยกแยะประเภทอุปกรณ์ทั้งหมดในภาพใหญ่ 1 ภาพ
2. **Crop & Route (Python Backend - Orchestrator):**
   *   สคริปต์ Python ใน Triton รับ Bbox มาทำการ **ตัดภาพ (Crop)** แบบ Dynamic
   *   กระจายงานแบบขนาน (Async/Parallel) ส่งภาพที่ตัดแล้วไปให้ Pipeline ย่อยตามประเภทของคลาส (เช่น โยนรูปเกจ 3 รูปให้ OCR, โยนรูปวาล์ว 2 รูปให้ Valve Classifier)
3. **Parallel Processing (Multiple Instances):**
   *   ในไฟล์ `config.pbtxt` ของโมเดลย่อย (เช่น OCR, Super Resolution) เราจะตั้งค่า `instance_group [ { count: 4, kind: KIND_GPU } ]` 
   *   เมื่อ Orchestrator ส่งภาพย่อยมาพร้อมกัน โมเดลจะสามารถประมวลผลหลายภาพได้ในเสี้ยววินาที

### ตัวอย่าง Code Flow สำหรับ Wide Scene:
```python
import triton_python_backend_utils as pb_utils
import asyncio

async def execute(self, requests):
    responses = []
    for request in requests:
        image = pb_utils.get_input_tensor_by_name(request, "image")
        
        # 1. ส่งภาพใหญ่เข้า Global Spotter
        global_req = pb_utils.InferenceRequest(model_name="global_detector", inputs=[image])
        global_res = await global_req.async_exec()
        detected_objects = parse_yolo_output(global_res) # ได้ Bbox และ Class
        
        # 2. เตรียมกระจายงาน (Dynamic Routing)
        tasks = []
        for obj in detected_objects:
            crop_img = crop(image, obj.bbox)
            
            if obj.class_name == "analog_gauge":
                tasks.append(process_analog_gauge_async(crop_img))
            elif obj.class_name == "flange":
                tasks.append(process_flange_async(crop_img))
            elif obj.class_name == "lever_valve":
                tasks.append(process_valve_async(crop_img))
                
        # 3. ประมวลผลโมเดลย่อยพร้อมกัน (ใช้ประโยขน์จาก Multiple Instances)
        inspection_results = await asyncio.gather(*tasks)
        
        # 4. คืนค่า JSON สรุปสถานะอุปกรณ์ทั้งหมดในภาพเดียว
        responses.append(pb_utils.InferenceResponse(output_tensors=[format_output(inspection_results)]))

    return responses
```

**สรุปฟันธง:** การเขียน Logic ตัดภาพและ If-else ฝังไว้ใน **Python Backend (BLS)** เพื่อลด Latency อินเทอร์เน็ต และการตั้งค่าโมเดล AI ย่อยให้เป็น **Multiple Instances** เพื่อเร่งความเร็วในการรันขนานแบบ Async คือ **Best Practice** สำหรับระบบหุ่นยนต์ตรวจสอบในโรงกลั่นครับ!
