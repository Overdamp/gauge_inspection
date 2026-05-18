import os
import json
import sys
from datetime import datetime

# เพิ่ม path เพื่อให้สามารถเรียกใช้ฟังก์ชันแปลงฟอร์แมตใน inference_proxy ได้
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from triton_integrated_client import run_inference_v8
from triton_integrated_client_grpc import run_inference_v8_grpc

def test_all_tasks():
    print("=" * 70)
    print("🧪 เริ่มต้นการทดสอบบีบีลและรับส่งข้อมูลครบทุกภารกิจ (Multi-Task Integration Test)")
    print("=" * 70)

    # รายการทดสอบครอบคลุมทุก Task ID (0, 1, 2, 3, 4, 5)
    tasks_to_test = [
        {
            "name": "Task 0: Digital Gauge (Mock)",
            "payload": {
                "inference_request_id": "req-digital-mock-001",
                "timestamp": datetime.now().isoformat(),
                "inference_task": 0,
                "inference_payload": json.dumps({"min_val": 0, "max_val": 200}),
                "image_uri": "/home/luke/gauge_inspection/images/analog-gauge/ag1.jpg"
            }
        },
        {
            "name": "Task 1: Analog Gauge (Actual Inference Pipeline)",
            "payload": {
                "inference_request_id": "req-analog-actual-001",
                "timestamp": datetime.now().isoformat(),
                "inference_task": 1,
                "inference_payload": json.dumps({"threshold_low": 20, "threshold_high": 80}),
                "image_uri": "/home/luke/gauge_inspection/images/analog-gauge/ag1.jpg"
            }
        },
        {
            "name": "Task 2: Engineering Abnormality (Mock)",
            "payload": {
                "inference_request_id": "req-abnormality-mock-001",
                "timestamp": datetime.now().isoformat(),
                "inference_task": 2,
                "inference_payload": "",
                "image_uri": "/home/luke/gauge_inspection/images/analog-gauge/ag1.jpg"
            }
        },
        {
            "name": "Task 3: Water Level Column (Mock)",
            "payload": {
                "inference_request_id": "req-water-mock-001",
                "timestamp": datetime.now().isoformat(),
                "inference_task": 3,
                "inference_payload": "",
                "image_uri": "/home/luke/gauge_inspection/images/analog-gauge/ag1.jpg"
            }
        },
        {
            "name": "Task 4: Gas Leakage (Mock)",
            "payload": {
                "inference_request_id": "req-gas-mock-001",
                "timestamp": datetime.now().isoformat(),
                "inference_task": 4,
                "inference_payload": "",
                "image_uri": "/home/luke/gauge_inspection/images/analog-gauge/ag1.jpg"
            }
        },
        {
            "name": "Task 5: Safety Incident Scanning (Mock)",
            "payload": {
                "inference_request_id": "req-safety-mock-001",
                "timestamp": datetime.now().isoformat(),
                "inference_task": 5,
                "inference_payload": "",
                "image_uri": "/home/luke/gauge_inspection/images/analog-gauge/ag1.jpg"
            }
        }
    ]

    # ล้างผลลัพธ์เก่าและทำความสะอาด Terminal
    os.makedirs("/home/luke/gauge_inspection/results/mock_tests", exist_ok=True)

    # 1. ทดสอบผ่านพอร์ต HTTP (8000)
    print("\n⚡ [1/2] เริ่มการทดสอบผ่านช่องทาง HTTP (Port 8000)")
    print("-" * 70)
    for t in tasks_to_test:
        print(f"\n▶️ กำลังทดสอบ {t['name']}...")
        try:
            res = run_inference_v8(t["payload"], triton_url="localhost:8000")
            print(f"✅ สำเร็จ! ผลลัพธ์ Payload C (HTTP):")
            print(json.dumps(res, indent=2, ensure_ascii=False))
            
            # บันทึกไฟล์ผลลัพธ์
            out_file = f"/home/luke/gauge_inspection/results/mock_tests/http_task_{t['payload']['inference_task']}.json"
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(res, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"❌ ล้มเหลว: {e}")

    # 2. ทดสอบผ่านพอร์ต gRPC (8001)
    print("\n⚡ [2/2] เริ่มการทดสอบผ่านช่องทาง gRPC (Port 8001)")
    print("-" * 70)
    for t in tasks_to_test:
        print(f"\n▶️ กำลังทดสอบ {t['name']}...")
        try:
            res = run_inference_v8_grpc(t["payload"], triton_url="localhost:8001")
            print(f"✅ สำเร็จ! ผลลัพธ์ Payload C (gRPC):")
            print(json.dumps(res, indent=2, ensure_ascii=False))
            
            # บันทึกไฟล์ผลลัพธ์
            out_file = f"/home/luke/gauge_inspection/results/mock_tests/grpc_task_{t['payload']['inference_task']}.json"
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(res, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"❌ ล้มเหลว: {e}")

    print("\n" + "=" * 70)
    print("🏁 เสร็จสิ้นการทดสอบครบทุกระบบ! ผลลัพธ์ถูกบันทึกไว้ใน results/mock_tests/")
    print("=" * 70)

if __name__ == "__main__":
    test_all_tasks()
