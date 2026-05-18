import json
import logging
from typing import Dict, Any, Optional

# ==========================================
# ส่วนของการตั้งค่าระบบ (Configuration)
# ==========================================

# ตั้งค่า Logger เพื่อแสดงข้อมูลการทำงานใน Terminal
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("ConvertInput")

# ตารางจับคู่ประเภทงาน (Task ID) กับชื่อโมเดล (Model Name) 
# อ้างอิงตามเอกสาร AI PTTEP.md (Payload B Section)
# การจับคู่ Task ID กับชื่อโมเดล และ Parameter สำหรับ Triton
TASK_CONFIG = {
    0: {"model": "task_digital_gauge_router", "triton_task": "digital_gauge"},
    1: {"model": "task_analog_gauge_router", "triton_task": "analog_gauge"},
    2: {"model": "task_abnormality_router", "triton_task": "abnormality"},
    3: {"model": "task_water_level_router", "triton_task": "water_level"},
    4: {"model": "task_gas_detection_router", "triton_task": "gas_detection"},
    5: {"model": "task_general_scan_router", "triton_task": "scanning"}
}

def convert_payload_a_to_b(payload_a: Dict[str, Any]) -> Dict[str, Any]:
    """
    ฟังก์ชันหลักในการแปลงข้อมูลจาก Payload A เป็น Payload B
    
    กระบวนการทำงาน (Step-by-Step):
    1. รับข้อมูลดิบ (Payload A) ที่ส่งมาจาก Robot หรือ CCR
    2. ดึงค่า inference_task เพื่อระบุประเภทงาน
    3. ตรวจสอบตาราง TASK_MODEL_MAPPING เพื่อระบุชื่อ Model ที่ต้องใช้งาน
    4. จัดการฟิลด์ inference_payload: 
       - หากเป็น String (JSON) จะต้องแปลงให้เป็น Dictionary (Object) เพื่อให้ระบบถัดไปใช้งานได้ง่าย
    5. สร้าง Dictionary ใหม่ (Payload B) ที่มีโครงสร้างตรงตาม Requirement ของ Inference Server
    """
    
    req_id = payload_a.get("inference_request_id", "N/A")
    task_id = payload_a.get("inference_task")
    
    logger.info(f"--- เริ่มกระบวนการแปลงข้อมูล [Request ID: {req_id}] ---")
    
    # ขั้นตอนที่ 1: ตรวจสอบโมเดลที่เกี่ยวข้อง
    config = TASK_CONFIG.get(task_id, {"model": "master_router", "triton_task": "unknown"})
    model_name = config["model"]
    triton_task = config["triton_task"]
    logger.info(f"1. จับคู่ Task ID {task_id} เข้ากับโมเดล: {model_name} (Triton Task: {triton_task})")
    
    # ขั้นตอนที่ 2: จัดการกับโครงสร้างข้อมูลเสริม (inference_payload)
    # ใน Payload A มักจะส่งมาเป็น String JSON เนื่องจากข้อจำกัดของระบบต้นทาง
    # เราต้องแปลงให้เป็น Python Object (Dictionary)
    inf_payload = payload_a.get("inference_payload")
    
    if isinstance(inf_payload, str) and inf_payload.strip():
        try:
            inf_payload = json.loads(inf_payload)
            logger.info("2. แปลง inference_payload จาก String เป็น Object สำเร็จ")
        except json.JSONDecodeError:
            logger.warning(f"2. [คำเตือน] ไม่สามารถ Parse JSON ใน inference_payload ได้: {inf_payload}")
    else:
        logger.info("2. ไม่พบข้อมูลใน inference_payload หรือข้อมูลอยู่ในรูปแบบที่ถูกต้องแล้ว")
    
    # ขั้นตอนที่ 3: ประกอบร่างเป็น Payload B ตาม Requirement
    payload_b = {
        "inference_request_id": req_id,
        "timestamp": payload_a.get("timestamp"),
        "inference_task": task_id,
        "inference_payload": inf_payload,
        "image_uri": payload_a.get("image_uri"),
        "model": model_name,
        "triton_task": triton_task
    }
    
    # ขั้นตอนที่ 4: ตรวจสอบและคัดลอกค่าคอนฟิกเสริม (ถ้ามี)
    # บางกรณีพารามิเตอร์อาจจะไม่อยู่ใน inference_payload แต่ถูกส่งมาในระดับบน
    for extra_key in ["threshold_low", "threshold_high"]:
        if extra_key in payload_a:
            payload_b[extra_key] = payload_a[extra_key]
            logger.info(f"3. พบค่าพารามิเตอร์เสริม: {extra_key}")

    logger.info("--- สิ้นสุดการแปลงข้อมูลสำเร็จ ---\n")
    return payload_b

# ==========================================
# ส่วนของการทดสอบ (Testing & Validation)
# ==========================================

def run_tests():
    """
    ฟังก์ชันสำหรับทดสอบความถูกต้อง (Requirement Validation)
    ครอบคลุมกรณีต่างๆ เพื่อให้มั่นใจว่าระบบทำงานได้ตามเป้าหมาย
    """
    print("="*60)
    print("ระบบทดสอบ Payload Conversion (A -> B)")
    print("="*60)

    # กรณีทดสอบที่ 1: การอ่านค่าเกจ (Analog Gauge) พร้อมพารามิเตอร์ Threshold
    print("[Test Case 1] Analog Gauge Reading (Task 1)")
    test_a_1 = {
        "inference_request_id": "uuid-001",
        "timestamp": "2026-03-26T19:20:05.112+07:00",
        "inference_task": 1,
        "inference_payload": "{\"threshold_low\":20,\"threshold_high\":80}",
        "image_uri": "s3://snapshots/gauge_test.png"
    }
    result_1 = convert_payload_a_to_b(test_a_1)
    
    # ตรวจสอบผลลัพธ์ตาม Requirement
    assert result_1["model"] == "master_router", "ผิดพลาด: Model ไม่ถูกต้อง"
    assert result_1["triton_task"] == "analog_gauge", "ผิดพลาด: Triton Task ไม่ถูกต้อง"
    assert isinstance(result_1["inference_payload"], dict), "ผิดพลาด: inference_payload ไม่ได้ถูกแปลงเป็น Object"
    print(json.dumps(result_1, indent=2, ensure_ascii=False))

    # กรณีทดสอบที่ 2: การตรวจจับความผิดปกติ (Abnormality Detection)
    print("\n[Test Case 2] Abnormality Detection (Task 2)")
    test_a_2 = {
        "inference_request_id": "uuid-002",
        "timestamp": "2026-03-26T20:00:00+07:00",
        "inference_task": 2,
        "inference_payload": None,
        "image_uri": "s3://snapshots/abnormality_test.png"
    }
    result_2 = convert_payload_a_to_b(test_a_2)
    assert result_2["model"] == "master_router"
    assert result_2["triton_task"] == "abnormality"
    assert result_2["inference_payload"] is None
    print(json.dumps(result_2, indent=2, ensure_ascii=False))

    print("\n" + "="*60)
    print("✅ สรุปผลการทดสอบ: ทุกกรณีทำงานได้ถูกต้องตาม Requirement")
    print("="*60)

if __name__ == "__main__":
    # รันการทดสอบอัตโนมัติ
    run_tests()
