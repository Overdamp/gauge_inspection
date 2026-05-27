import cv2
import json
import numpy as np
import tritonclient.http as httpclient
import sys
import os
import glob
import time

def test_triton_batch():
    url = "localhost:8000"  # HTTP port
    model_name = "task_analog_gauge_router"

    input_dir = "/home/luke/gauge_inspection/images/analog-gauge"
    output_dir = "/home/luke/gauge_inspection/results/triton_results"
    os.makedirs(output_dir, exist_ok=True)

    # ค้นหาไฟล์ภาพทั้งหมด
    valid_extensions = ('*.jpg', '*.jpeg', '*.png', '*.bmp')
    image_paths = []
    for ext in valid_extensions:
        image_paths.extend(glob.glob(os.path.join(input_dir, ext)))
        image_paths.extend(glob.glob(os.path.join(input_dir, ext.upper())))
    
    image_paths = sorted(image_paths)

    if not image_paths:
        print(f"❌ ไม่พบรูปภาพใน {input_dir}")
        return

    print(f"Connecting to Triton Server at {url} (HTTP)...")
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
        
        if img is None:
            print(f"❌ [{filename}] อ่านไฟล์ภาพไม่สำเร็จ")
            continue

        # เตรียมข้อมูลภาพ [1, H, W, 3]
        img_batch = np.expand_dims(img, axis=0)
        
        # Prepare inputs
        inputs = [
            httpclient.InferInput("IMAGE", img_batch.shape, "UINT8"),
        ]
        inputs[0].set_data_from_numpy(img_batch)

        # Parameters
        request_params = {"TASK_TYPE": "analog_gauge"}

        # Outputs
        outputs = [
            httpclient.InferRequestedOutput("JSON_RESULT"),
            httpclient.InferRequestedOutput("VISUALIZED_IMAGE")
        ]

        try:
            # Inference
            response = client.infer(
                model_name=model_name, 
                inputs=inputs, 
                outputs=outputs, 
                parameters=request_params
            )
            
            json_data = response.as_numpy("JSON_RESULT")
            vis_data = response.as_numpy("VISUALIZED_IMAGE")
            
            if json_data is None or vis_data is None:
                print(f"❌ [{filename}] Triton ส่งข้อมูลกลับมาเป็นค่าว่าง")
                continue

            # Parse JSON
            json_str = json_data[0].decode('utf-8') if isinstance(json_data[0], bytes) else str(json_data[0])
            results = json.loads(json_str)
            
            if "value" in results:
                unit = results.get("unit", "")
                r2 = results.get("r2_score", 0)
                pts = results.get("fit_points", 0)
                slope = results.get("slope", 0)
                direction = "CW" if slope > 0 else "CCW"
                
                print(f"✅ [{filename}] Read: {results['value']:.2f} {unit} | R²={r2:.2f} | pts={pts} | {direction}")
                success_count += 1
            else:
                print(f"⚠️ [{filename}] Error: {results.get('error', 'Unknown error')}")

            # บันทึก JSON
            output_json_path = os.path.join(output_dir, f"result_{filename}.json")
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=4, ensure_ascii=False)
                
            # บันทึกภาพ
            img_bytes_out = vis_data[0]
            if isinstance(img_bytes_out, (bytes, bytearray)) and len(img_bytes_out) > 0:
                nparr = np.frombuffer(img_bytes_out, np.uint8)
                vis_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if vis_img is not None:
                    output_image_path = os.path.join(output_dir, f"result_{filename}")
                    cv2.imwrite(output_image_path, vis_img)

        except Exception as e:
            print(f"❌ [{filename}] Error during inference: {e}")

    total_time = time.time() - start_time
    print("-" * 50)
    print(f"🏁 Processing Completed!")
    print(f"📊 Successfully processed {success_count}/{len(image_paths)} images")
    print(f"⏱️ Total time: {total_time:.2f} seconds ({total_time/len(image_paths):.2f}s per image)")
    print(f"📂 Results saved to: {output_dir}")

if __name__ == "__main__":
    test_triton_batch()