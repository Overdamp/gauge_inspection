import os
import sys
from ultralytics import YOLO

def convert_yolo_to_trt(model_path, imgsz=640):
    if not os.path.exists(model_path):
        print(f"❌ Model not found at: {model_path}")
        return

    print(f"📦 Loading model: {model_path}")
    model = YOLO(model_path)

    print(f"🚀 Exporting to TensorRT (imgsz={imgsz})...")
    # การส่งออกเป็น TensorRT (.engine)
    # half=True จะช่วยใช้ FP16 เพื่อความเร็ว (ถ้า GPU รองรับ)
    try:
        path = model.export(
            format='engine', 
            imgsz=imgsz, 
            device=0, 
            half=True,
            simplify=True
        )
        print(f"✅ Export successful! Engine saved at: {path}")
    except Exception as e:
        print(f"❌ Export failed: {e}")

if __name__ == "__main__":
    # ระบุ Path ของโมเดลที่ต้องการแปลง
    target_model = "/home/luke/gauge_inspection/models/analog_gauge_model/segmentation/best_segment_v2.pt"
    
    # รันการแปลง
    convert_yolo_to_trt(target_model)
