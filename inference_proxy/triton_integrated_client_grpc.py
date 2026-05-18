import cv2
import json
import numpy as np
import tritonclient.grpc as grpcclient
import sys
import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# เพิ่ม path เพื่อให้ import สคริปต์ในโฟลเดอร์เดียวกันได้
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from convert_input import convert_payload_a_to_b
from convert_output import convert_triton_to_payload_c

def run_inference_v8_grpc(payload_a: dict, triton_url: str = "localhost:8001"):
    """
    ฟังก์ชันแบบ End-to-End (gRPC Version):
    1. รับ Payload A (มาตรฐาน Robot/CCR)
    2. แปลงเป็น Payload B
    3. ส่งไปที่ Triton Server ผ่าน gRPC (Port 8001)
    4. แปลงกลับเป็น Payload C (Version 8)
    """
    
    # --- Step 1: Pre-process (A -> B) ---
    payload_b = convert_payload_a_to_b(payload_a)
    model_name = payload_b["model"]
    triton_task = payload_b["triton_task"]
    image_uri = payload_b["image_uri"]
    
    print(f"🚀 [gRPC PRE-PROCESS] Payload A -> B: Model={model_name}, Task={triton_task}")

    # --- Step 2: Prepare Image Data ---
    if not os.path.exists(image_uri):
        return {"error": f"Image file not found: {image_uri}"}
        
    img = cv2.imread(image_uri)
    if img is None:
        return {"error": f"Failed to read image: {image_uri}"}
    
    img_batch = np.expand_dims(img, axis=0).astype(np.uint8)

    # --- Step 3: Triton Inference via gRPC ---
    print(f"📡 [gRPC] Connecting to {triton_url}...")
    try:
        # ใช้ grpcclient แทน httpclient
        client = grpcclient.InferenceServerClient(url=triton_url)
        
        # เตรียม Input Tensors (ใช้ grpcclient)
        inputs = [
            grpcclient.InferInput("IMAGE", img_batch.shape, "UINT8"),
        ]
        inputs[0].set_data_from_numpy(img_batch)

        # ระบุ Outputs ที่ต้องการ
        outputs = [
            grpcclient.InferRequestedOutput("JSON_RESULT"),
        ]

        # เตรียม Parameters
        request_params = {"TASK_TYPE": triton_task}

        # เรียกใช้งาน Inference
        response = client.infer(
            model_name=model_name,
            inputs=inputs,
            outputs=outputs,
            client_timeout=30.0, # ตั้งเวลา Timeout ไว้ 30 วินาที
            parameters=request_params
        )

        # ดึงผลลัพธ์ดิบออกมา
        json_data = response.as_numpy("JSON_RESULT")
        if json_data is None:
            return {"error": "Triton returned empty JSON_RESULT"}

        # แปลง bytes เป็น Python Dict
        json_str = json_data[0].decode('utf-8') if isinstance(json_data[0], bytes) else str(json_data[0])
        triton_raw_result = json.loads(json_str)
        print(f"✅ [gRPC] Raw Result Received")

    except Exception as e:
        print(f"❌ [gRPC ERROR] Triton Inference failed: {e}")
        triton_raw_result = {"error": str(e)}

    # --- Step 4: Post-process (Triton -> C v8) ---
    print(f"📦 [POST-PROCESS] Mapping result to Payload C Version 8...")
    payload_c = convert_triton_to_payload_c(triton_raw_result, payload_b)
    
    return payload_c

# --- ส่วนของ API Server (ยังคงใช้ Flask รับ HTTP จากภายนอก) ---
app = Flask(__name__)
CORS(app)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        payload_a = request.get_json()
        if not payload_a:
            return jsonify({"error": "No JSON payload provided"}), 400
        
        # เรียกใช้ฟังก์ชัน gRPC ภายใน
        result = run_inference_v8_grpc(payload_a)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def start_server(port=5000):
    print(f"\n" + "="*50)
    print(f"🚀 AI INFERENCE PROXY (gRPC-INTERNAL) IS RUNNING")
    print(f"External API: http://localhost:{port}/predict (HTTP)")
    print(f"Internal Triton: localhost:8001 (gRPC)")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    if "--server" in sys.argv:
        start_server()
    elif len(sys.argv) > 1:
        # โหมดไฟล์ JSON
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            test_payload_a = json.load(f)
        result = run_inference_v8_grpc(test_payload_a)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # โหมด Default Mockup
        print("💡 [INFO] Running Inference Proxy in default mode. Use '--server' to start API.")
        test_payload_a = {
            "inference_request_id": "grpc-default-test",
            "timestamp": datetime.now().isoformat(),
            "inference_task": 1,
            "image_uri": "/home/luke/gauge_inspection/images/analog-gauge/ag1.jpg"
        }
        result = run_inference_v8_grpc(test_payload_a)
        print(json.dumps(result, indent=2, ensure_ascii=False))
