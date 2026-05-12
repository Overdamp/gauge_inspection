import cv2
import json
import numpy as np
import tritonclient.grpc as grpcclient  # 🌟 เปลี่ยนมาใช้ grpc
import sys
import os
import glob

def test_triton_grpc():
    url = "localhost:8001"  # 🌟 เปลี่ยนพอร์ตเป็น 8001 สำหรับ gRPC
    model_name = "master_router"

    input_dir = "/home/luke/gauge_inspection/images/analog-gauge"
    output_dir = "/home/luke/gauge_inspection/results/triton_results"
    os.makedirs(output_dir, exist_ok=True)

    # รองรับการระบุชื่อไฟล์ผ่าน Command Line (เช่น รูป ag2.jpg)
    if len(sys.argv) > 1:
        test_image_path = sys.argv[1]
    else:
        image_files = sorted(glob.glob(os.path.join(input_dir, "*.*")))
        if not image_files:
            print(f"❌ ไม่พบรูปภาพใน {input_dir}")
            return
        test_image_path = image_files[4]
        
    img = cv2.imread(test_image_path)
    if img is None:
        print(f"❌ อ่านไฟล์ภาพไม่สำเร็จ: {test_image_path}")
        return

    print(f"Connecting to Triton Server at {url} (gRPC)...")
    try:
        client = grpcclient.InferenceServerClient(url=url)
    except Exception as e:
        print(f"❌ Error connecting to Triton: {e}")
        return

    # Resize to 640x640 and send as UINT8 tensor
    img_resized = cv2.resize(img, (640, 640))
    img_batch = np.expand_dims(img_resized, axis=0)  # [1, 640, 640, 3]
    
    print(f"🔍 ภาพดั้งเดิม Shape = {img.shape}, ส่งเป็น Shape = {img_batch.shape}")

    # Prepare inputs - 🌟 ใช้ grpcclient
    inputs = [
        grpcclient.InferInput("IMAGE", img_batch.shape, "UINT8"),
    ]
    inputs[0].set_data_from_numpy(img_batch)

    # Send TASK_TYPE as request parameter
    request_params = {"TASK_TYPE": "analog_gauge"}

    # Prepare outputs - 🌟 ใช้ grpcclient
    outputs = [
        grpcclient.InferRequestedOutput("JSON_RESULT"),
        grpcclient.InferRequestedOutput("VISUALIZED_IMAGE")
    ]

    print(f"กำลังส่งภาพ {os.path.basename(test_image_path)} ไปให้ Triton ประมวลผล (gRPC)...")
    
    try:
        # การรัน infer ของ gRPC ใช้ syntax เหมือน HTTP ทุกประการ
        response = client.infer(model_name=model_name, inputs=inputs, outputs=outputs, parameters=request_params)
        
        json_data = response.as_numpy("JSON_RESULT")
        vis_data = response.as_numpy("VISUALIZED_IMAGE")
        
        if json_data is None or vis_data is None:
            print("❌ Triton ส่งข้อมูลกลับมาเป็นค่าว่าง (None)")
            return

        print(f"✅ ฝั่ง Server ตอบกลับสำเร็จผ่าน gRPC!")
        
        # Parse JSON result
        json_str = json_data[0].decode('utf-8') if isinstance(json_data[0], bytes) else str(json_data[0])
        results = json.loads(json_str)
        
        if "value" in results:
            unit = results.get("unit", "")
            r2 = results.get("r2_score", 0)
            print(f"🎯 ผลลัพธ์การอ่านเข็ม: {results['value']:.2f} {unit}  (R²={r2:.2f})")
        else:
            print(f"⚠️ ผลลัพธ์ JSON: {results}")

        output_json_path = os.path.join(output_dir, f"grpc_result_{os.path.basename(test_image_path)}.json")
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
        print(f"✅ บันทึกข้อมูล JSON สำเร็จที่: {output_json_path}")
            
        # Decode JPEG image from response
        img_bytes_out = vis_data[0]
        if isinstance(img_bytes_out, (bytes, bytearray)) and len(img_bytes_out) > 0:
            nparr = np.frombuffer(img_bytes_out, np.uint8)
            vis_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if vis_img is not None:
                output_image_path = os.path.join(output_dir, f"grpc_result_{os.path.basename(test_image_path)}")
                cv2.imwrite(output_image_path, vis_img)
                print(f"✅ บันทึกภาพผลลัพธ์สำเร็จที่: {output_image_path}")
            else:
                print("❌ ไม่สามารถ Decode ภาพจาก Bytes ได้")

    except Exception as e:
        import traceback
        print(f"\n❌ [Error]:\n{traceback.format_exc()}")

if __name__ == "__main__":
    test_triton_grpc()