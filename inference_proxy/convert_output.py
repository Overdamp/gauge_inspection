import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# ==========================================
# ส่วนของการตั้งค่าระบบ (Configuration)
# ==========================================

# ตั้งค่า Logger เพื่อแสดงข้อมูลการทำงานใน Terminal
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("ConvertOutput")

def convert_triton_to_payload_c(
    triton_out: Dict[str, Any], 
    request_metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    ฟังก์ชันหลักในการแปลงผลลัพธ์ดิบจาก AI (Triton) ให้เป็นมาตรฐาน Payload C (Version 8)
    
    กระบวนการทำงาน (Step-by-Step):
    1. สร้างโครงสร้างหลัก (Common Envelope): ใส่ metadata อ้างอิงจากคำขอต้นทาง (Request Metadata)
    2. สร้างรายการผลลัพธ์ (Result Item): 
       - กำหนดค่าเริ่มต้น เช่น detection_id = 1 และสถานะ SUCCESS
       - จับคู่ Task ID กับประเภทวัตถุ (Object Type)
    3. ตรวจสอบข้อผิดพลาด (Error Handling): หากโมเดลส่ง error มา จะเปลี่ยนสถานะเป็น FAILED และใส่รายละเอียดลงใน inference_error
    4. จัดรูปแบบผลลัพธ์มาตรฐาน (Standardized Outputs):
       - ย้ายค่าผลลัพธ์หลัก (เช่น value) ไปไว้ใน outputs object แบบแบน (Flat Object)
       - ย้ายข้อมูลเชิงคณิตศาสตร์หรือการดีบั๊กไปไว้ใน debug object
    5. ส่งคืนข้อมูลในรูปแบบ Version 8 Schema ที่สมบูรณ์
    """
    
    req_id = request_metadata.get("inference_request_id", "N/A")
    task_id = request_metadata.get("inference_task")
    
    logger.info(f"--- เริ่มกระบวนการแปลงผลลัพธ์ [Request ID: {req_id}] ---")
    
    # ขั้นตอนที่ 1: สร้างโครงสร้างส่วนห่อหุ้ม (Envelope)
    payload_c = {
        "inference_request_id": req_id,
        "timestamp": datetime.now().isoformat() + "+07:00", 
        "image_uri": request_metadata.get("image_uri"),
        "inference_task": task_id,
        "results": []
    }
    
    # ขั้นตอนที่ 2: กำหนดโครงสร้างไอเทมผลลัพธ์ (ตาม Version 8 Standard)
    result_item = {
        "detection_id": 1,
        "inference_status": "SUCCESS",
        "inference_error": None,
        "object_type": _map_task_to_object_type(task_id),
        "object_condition": "NORMAL", # ค่าเริ่มต้น
        "primary_detection": {
            "class_name": _map_task_to_object_type(task_id),
            "confidence": 1.0,
            "bbox": [0, 0, 0, 0] # Mocked if not provided by model
        },
        "components": {},
        "ocr": [],
        "outputs": {},
        "feedback": [],
        "debug": {}
    }
    
    # ขั้นตอนที่ 3: ตรวจสอบกรณีโมเดลทำงานไม่สำเร็จ
    if "error" in triton_out:
        logger.error(f"1. พบข้อผิดพลาดจากโมเดล: {triton_out['error']}")
        result_item["inference_status"] = "FAILED"
        result_item["object_condition"] = None
        result_item["inference_error"] = {
            "code": "MODEL_INFERENCE_ERROR",
            "message": triton_out["error"],
            "stage": "inference"
        }
    else:
        # ขั้นตอนที่ 4: การจับคู่ข้อมูลเฉพาะตามประเภทงาน (Task Mapping)
        logger.info(f"1. กำลังประมวลผลข้อมูลสำหรับ Task ID: {task_id}")
        
        if task_id in [0, 1]: # กลุ่มงานอ่านค่าเกจ
            # นำข้อมูลดิบมาใส่ในโครงสร้าง outputs ที่กำหนดไว้ใน V8
            result_item["outputs"] = {
                "gauge_reading": triton_out.get("value"),
                "unit": triton_out.get("unit"),
                "confidence": triton_out.get("confidence", 0.95),
                "gauge_level": triton_out.get("gauge_level", "Normal")
            }
            # แยกข้อมูลเชิงลึกไปที่ debug
            result_item["debug"] = {
                "r2_score": triton_out.get("r2_score"),
                "fit_points": triton_out.get("fit_points"),
                "needle_tip": triton_out.get("needle_tip")
            }
            logger.info(f"2. อ่านค่าเกจสำเร็จ: {result_item['outputs']['gauge_reading']}")

        elif task_id == 2: # การตรวจจับความผิดปกติ
            result_item["object_condition"] = triton_out.get("object_condition", "ABNORMAL")
            result_item["outputs"] = {
                "abnormality_type": triton_out.get("abnormality_type"),
                "severity": triton_out.get("severity"),
                "confidence": triton_out.get("confidence")
            }
            logger.info(f"2. ตรวจพบความผิดปกติ: {result_item['outputs']['abnormality_type']}")

        elif task_id == 3: # ระดับน้ำ
            result_item["outputs"] = {
                "water_level": triton_out.get("water_level"),
                "sump_type": triton_out.get("sump_type"),
                "confidence": triton_out.get("confidence")
            }
            logger.info(f"2. ตรวจวัดระดับน้ำสำเร็จ: {result_item['outputs']['water_level']}")

        elif task_id == 4: # ก๊าซรั่ว (Gas Detection)
            result_item["outputs"] = {
                "gas_detected": triton_out.get("gas_detected", False),
                "confidence": triton_out.get("confidence")
            }
            logger.info(f"2. ตรวจสอบก๊าซรั่วสำเร็จ: {result_item['outputs']['gas_detected']}")

        elif task_id == 5: # ไฟ/ควัน (Fire/Smoke)
            result_item["outputs"] = {
                "fire_detected": triton_out.get("fire_detected", False),
                "smoke_detected": triton_out.get("smoke_detected", False),
                "confidence": triton_out.get("confidence")
            }
            logger.info(f"2. ตรวจสอบไฟ/ควันสำเร็จ: {result_item['outputs']['fire_detected']}")

    # ขั้นตอนที่ 5: บรรจุลงใน List และส่งคืน
    payload_c["results"].append(result_item)
    logger.info("--- สิ้นสุดการแปลงผลลัพธ์สำเร็จ ---\n")
    return payload_c

def _map_task_to_object_type(task_id: int) -> str:
    """ผู้ช่วยในการระบุประเภทวัตถุตามมาตรฐานโครงการ"""
    mapping = {
        0: "digital_gauge",
        1: "analog_gauge",
        2: "inspected_object",
        3: "sump",
        4: "gas_monitoring_area",
        5: "safety_incident_area",
        6: "ocr_target"
    }
    return mapping.get(task_id, "unknown")

# ==========================================
# ส่วนของการทดสอบ (Testing & Validation)
# ==========================================

def run_tests():
    """
    ฟังก์ชันสำหรับทดสอบความถูกต้อง (Requirement Validation)
    เพื่อให้มั่นใจว่าโครงสร้างที่ส่งออกไปตรงตาม Payload C Version 8
    """
    print("="*60)
    print("ระบบทดสอบ Payload Conversion (Triton -> C v8)")
    print("="*60)

    # กรณีทดสอบที่ 1: ผลลัพธ์การอ่านเกจสำเร็จ (SUCCESS Case)
    print("[Test Case 1] Analog Gauge SUCCESS Mapping")
    sample_triton = {
        "value": 45.2,
        "unit": "bar",
        "r2_score": 0.98,
        "gauge_level": "Normal"
    }
    meta = {
        "inference_request_id": "req-ok-001",
        "inference_task": 1,
        "image_uri": "s3://snapshots/gauge.jpg"
    }
    result_c = convert_triton_to_payload_c(sample_triton, meta)
    
    # ตรวจสอบโครงสร้างหลัก
    assert "results" in result_c
    assert result_c["results"][0]["inference_status"] == "SUCCESS"
    assert result_c["results"][0]["outputs"]["gauge_reading"] == 45.2
    print(json.dumps(result_c, indent=2, ensure_ascii=False))

    # กรณีทดสอบที่ 2: โมเดลทำงานล้มเหลว (FAILED Case)
    print("\n[Test Case 2] Model Failure Handling")
    fail_triton = {
        "error": "Cannot locate needle in the image"
    }
    result_fail = convert_triton_to_payload_c(fail_triton, meta)
    
    assert result_fail["results"][0]["inference_status"] == "FAILED"
    assert result_fail["results"][0]["inference_error"]["code"] == "MODEL_INFERENCE_ERROR"
    print(json.dumps(result_fail, indent=2, ensure_ascii=False))

    print("\n" + "="*60)
    print("✅ สรุปผลการทดสอบ: ผลลัพธ์ตรงตามโครงสร้าง Version 8 อย่างสมบูรณ์")
    print("="*60)

if __name__ == "__main__":
    # รันการทดสอบอัตโนมัติ
    run_tests()
