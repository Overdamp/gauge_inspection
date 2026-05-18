import cv2
import json
import numpy as np
import tritonclient.http as httpclient
import sys
import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# เพิ่ม path เพื่อให้ import สคริปต์ในโฟลเดอร์เดียวกันได้
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from convert_input import convert_payload_a_to_b
from convert_output import convert_triton_to_payload_c

def run_inference_v8(payload_a: dict, triton_url: str = "localhost:8000"):
    """
    ฟังก์ชันแบบ End-to-End:
    1. รับ Payload A (มาตรฐาน Robot/CCR)
    2. แปลงเป็น Payload B (ดึง Model และ Task Type)
    3. ส่งรูปภาพและพารามิเตอร์ไปที่ Triton Server
    4. รับผลลัพธ์ดิบแล้วแปลงกลับเป็น Payload C (Version 8 Standard)
    """
    
    # --- Step 1: Pre-process (A -> B) ---
    payload_b = convert_payload_a_to_b(payload_a)
    model_name = payload_b["model"]
    triton_task = payload_b["triton_task"]
    image_uri = payload_b["image_uri"]
    
    print(f"🚀 [PRE-PROCESS] Payload A -> B: Model={model_name}, Task={triton_task}")

    # --- Step 2: Prepare Image Data ---
    # ในตัวอย่างนี้สมมติว่า image_uri เป็นพาธในเครื่อง (Local Path)
    # หากเป็น S3 จะต้องมีโค้ดส่วนการดาวน์โหลดเพิ่มตรงนี้
    if not os.path.exists(image_uri):
        return {"error": f"Image file not found: {image_uri}"}
        
    img = cv2.imread(image_uri)
    if img is None:
        return {"error": f"Failed to read image: {image_uri}"}
    
    # Triton คาดหวังมิติภาพแบบ [Batch, Height, Width, Channels]
    img_batch = np.expand_dims(img, axis=0)

    # --- Step 3: Triton Inference ---
    print(f"📡 [TRITON] Connecting to {triton_url}...")
    try:
        client = httpclient.InferenceServerClient(url=triton_url)
        
        # เตรียม Input Tensors
        inputs = [
            httpclient.InferInput("IMAGE", img_batch.shape, "UINT8"),
        ]
        inputs[0].set_data_from_numpy(img_batch)

        # เตรียม Parameters (ส่ง Task Type ไปที่ Master Router)
        request_params = {"TASK_TYPE": triton_task}

        # ระบุ Outputs ที่ต้องการ
        outputs = [
            httpclient.InferRequestedOutput("JSON_RESULT"),
            httpclient.InferRequestedOutput("VISUALIZED_IMAGE") # (ไม่ได้ใช้ใน Payload C แต่ดึงมาดูได้)
        ]

        # เรียกใช้งาน Inference
        response = client.infer(
            model_name=model_name,
            inputs=inputs,
            outputs=outputs,
            parameters=request_params
        )

        # ดึงผลลัพธ์ดิบออกมา
        json_data = response.as_numpy("JSON_RESULT")
        if json_data is None:
            return {"error": "Triton returned empty JSON_RESULT"}

        # แปลง bytes เป็น Python Dict
        json_str = json_data[0].decode('utf-8') if isinstance(json_data[0], bytes) else str(json_data[0])
        triton_raw_result = json.loads(json_str)
        print(f"✅ [TRITON] Raw Result Received")

    except Exception as e:
        print(f"❌ [ERROR] Triton Inference failed: {e}")
        triton_raw_result = {"error": str(e)}

    # --- Step 4: Post-process (Triton -> C v8) ---
    print(f"📦 [POST-PROCESS] Mapping result to Payload C Version 8...")
    payload_c = convert_triton_to_payload_c(triton_raw_result, payload_b)
    
    return payload_c

# --- ส่วนของ API Server ---
app = Flask(__name__)
CORS(app) # อนุญาตให้เข้าถึงจาก Domain อื่นได้

@app.route('/predict', methods=['POST'])
def predict():
    """
    Endpoint สำหรับรับ Payload A ผ่าน HTTP POST
    ตัวอย่างการยิงจาก Postman: POST http://localhost:5000/predict
    Body: JSON (Payload A)
    """
    try:
        payload_a = request.get_json()
        if not payload_a:
            return jsonify({"error": "No JSON payload provided"}), 400
        
        # รันกระบวนการ Inference
        result = run_inference_v8(payload_a)
        
        # ส่งผลลัพธ์กลับไปเป็น JSON (Payload C)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def start_server(port=5000):
    print(f"\n" + "="*50)
    print(f"🚀 AI INFERENCE PROXY (HTTP-API) IS RUNNING")
    print(f"URL: http://localhost:{port}/predict")
    print(f"Method: POST")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    # เช็คว่าผู้ใช้ต้องการเปิด Server หรือประมวลผลไฟล์เดียว
    if "--server" in sys.argv:
        start_server()
    
    elif len(sys.argv) > 1:
        # โหมดประมวลผลจากไฟล์ JSON
        json_file_path = sys.argv[1]
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r', encoding='utf-8') as f:
                test_payload_a = json.load(f)
            print(f"📄 [INPUT] Loaded Payload A from: {json_file_path}")
            
            final_result = run_inference_v8(test_payload_a)
            print("\n" + "="*50)
            print("FINAL STANDARDIZED RESPONSE (PAYLOAD C)")
            print("="*50)
            print(json.dumps(final_result, indent=2, ensure_ascii=False))
        else:
            print(f"❌ [ERROR] File not found: {json_file_path}")
    
    else:
        # โหมด Default Mockup
        print("💡 [INFO] Running Inference Proxy in default mode. Use '--server' to start API.")
        test_payload_a = {
            "inference_request_id": "default-test-001",
            "timestamp": datetime.now().isoformat(),
            "inference_task": 1,
            "inference_payload": json.dumps({"threshold_low": 20, "threshold_high": 80}),
            "image_uri": "/home/luke/gauge_inspection/images/analog-gauge/ag1.jpg"
        }
        final_result = run_inference_v8(test_payload_a)
        print(json.dumps(final_result, indent=2, ensure_ascii=False))
