# 🛠 Model Conversion Guide (TensorRT)

โฟลเดอร์นี้ใช้สำหรับรวบรวมสคริปต์ในการแปลงโมเดลจาก PyTorch (`.pt`, `.pth`) ให้เป็น **TensorRT (`.engine`)** เพื่อเพิ่มประสิทธิภาพในการทำ Inference บน NVIDIA GPU

---

## 🚀 ขั้นตอนการใช้งาน

การแปลงโมเดลต้องทำในสภาพแวดล้อมที่มี TensorRT และ CUDA ติดตั้งอยู่ แนะนำให้รันผ่าน **Triton Docker Container**:

```bash
# 1. เข้าไปใน Container
docker exec -it triton_bls bash

# 2. ย้ายไปที่โฟลเดอร์โปรเจค
cd /home/luke/gauge_inspection
```

### 1. การแปลง Segmentation (YOLOv8)
ใช้สคริปต์ `convert_yolo.py` เพื่อแปลงเป็นไฟล์ `.engine` โดยตรง:
```bash
python3 model_conversion/convert_yolo.py
```
*ผลลัพธ์จะถูกสร้างไว้ที่โฟลเดอร์เดียวกับโมเดลต้นทาง*

### 2. การแปลง OCR (DocTR)
การแปลง OCR ต้องทำ 2 ขั้นตอน:
1.  **Export เป็น ONNX**:
    ```bash
    python3 model_conversion/convert_ocr.py
    ```
2.  **Convert ONNX เป็น Engine** (ใช้เครื่องมือ `trtexec` ที่มีมาใน Triton Container):
    ```bash
    trtexec --onnx=model_conversion/ocr_model.onnx \
            --saveEngine=models/analog_gauge_model/ocr/best_model.engine \
            --fp16
    ```

---

## 📝 รายละเอียดสคริปต์
*   **`convert_yolo.py`**: ใช้ Ultralytics API ในการ Export (รองรับ FP16 และ Dynamic Shapes)
*   **`convert_ocr.py`**: โหลดสถาปัตยกรรม DocTR และ Export ผ่าน `torch.onnx`

## ⚠️ ข้อควรระวัง
*   ไฟล์ `.engine` ที่ได้จะ **ผูกกับรุ่นของ GPU และเวอร์ชันของ TensorRT** ที่ใช้รันสคริปต์ หากย้ายไปเครื่องอื่นที่มี GPU ต่างรุ่นกัน อาจต้องทำการแปลงใหม่
*   แนะนำให้เปิดโหมด **FP16** (Half Precision) เพื่อให้ได้ความเร็วสูงสุดโดยที่ความแม่นยำแทบไม่ลดลง
