import cv2
import json
import numpy as np
import tritonclient.http as httpclient
import sys
import os
import glob
import time

def test_triton_version(version="2"):
    url = "localhost:8000"  # HTTP port
    model_name = "task_analog_gauge_router"
    model_version = version # เลือก version ได้ที่นี่ ("1" หรือ "2")

    input_dir = "/home/luke/gauge_inspection/images/analog-gauge"
    output_dir = f"/home/luke/gauge_inspection/results/triton_results_v{version}"
    os.makedirs(output_dir, exist_ok=True)

    image_paths = sorted(glob.glob(os.path.join(input_dir, "*.*")))
    if not image_paths:
        print(f"❌ ไม่พบรูปภาพใน {input_dir}")
        return

    print(f"Connecting to Triton Server at {url} (HTTP)...")
    print(f"Testing Model: {model_name} Version: {model_version}")
    try:
        client = httpclient.InferenceServerClient(url=url)
    except Exception as e:
        print(f"❌ Error connecting to Triton: {e}")
        return

    print(f"🚀 Found {len(image_paths)} images. Starting batch processing...")
    print("-" * 50)

    start_time = time.time()
    success_count = 0

    for img_path in image_paths:
        filename = os.path.basename(img_path)
        img = cv2.imread(img_path)
        if img is None: continue

        img_batch = np.expand_dims(img, axis=0)
        inputs = [httpclient.InferInput("IMAGE", img_batch.shape, "UINT8")]
        inputs[0].set_data_from_numpy(img_batch)
        request_params = {"TASK_TYPE": "analog_gauge"}
        outputs = [
            httpclient.InferRequestedOutput("JSON_RESULT"),
            httpclient.InferRequestedOutput("VISUALIZED_IMAGE")
        ]

        try:
            # ระบุ model_version ในการเรียก infer
            response = client.infer(
                model_name=model_name, 
                model_version=model_version,
                inputs=inputs, 
                outputs=outputs, 
                parameters=request_params
            )
            
            json_data = response.as_numpy("JSON_RESULT")
            vis_data = response.as_numpy("VISUALIZED_IMAGE")
            
            json_str = json_data[0].decode('utf-8') if isinstance(json_data[0], bytes) else str(json_data[0])
            results = json.loads(json_str)
            
            if "value" in results:
                unit = results.get("unit", "")
                r2 = results.get("r2_score", 0)
                print(f"✅ [{filename}] Read: {results['value']:.2f} {unit} (R²={r2:.2f})")
                success_count += 1
            else:
                print(f"⚠️ [{filename}] Error: {results.get('error', 'Unknown')}")

            # # บันทึกภาพ (คอมเมนต์ออกเพื่อความเร็ว)
            # img_bytes_out = vis_data[0]
            # if isinstance(img_bytes_out, (bytes, bytearray)) and len(img_bytes_out) > 0:
            #     nparr = np.frombuffer(img_bytes_out, np.uint8)
            #     vis_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            #     if vis_img is not None:
            #         cv2.imwrite(os.path.join(output_dir, f"result_{filename}"), vis_img)

        except Exception as e:
            print(f"❌ [{filename}] Error: {e}")

    total_time = time.time() - start_time
    print("-" * 50)
    print(f"🏁 Finished Version {version}! Success: {success_count}/{len(image_paths)} | Time: {total_time:.2f}s")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ver = sys.argv[1]
    else:
        ver = "2"
    test_triton_version(ver)
