import cv2
import numpy as np
import time
import tritonclient.http as httpclient
import tritonclient.grpc as grpcclient

def run_benchmark(protocol="grpc", num_requests=50):
    model_name = "master_router"
    image_path = "/home/luke/gauge_inspection/images/analog-gauge/ag1.jpg"
    
    # 1. เตรียมรูปภาพ (ทำครั้งเดียวจะได้ไม่เอาเวลาประมวลผลภาพมารวม)
    img = cv2.imread(image_path)
    img_resized = cv2.resize(img, (640, 640))
    img_batch = np.expand_dims(img_resized, axis=0)
    request_params = {"TASK_TYPE": "analog_gauge"}

    # 2. ตั้งค่า Client ตาม Protocol
    if protocol == "http":
        client = httpclient.InferenceServerClient(url="localhost:8000")
        inputs = [httpclient.InferInput("IMAGE", img_batch.shape, "UINT8")]
        outputs = [
            httpclient.InferRequestedOutput("JSON_RESULT"),
            httpclient.InferRequestedOutput("VISUALIZED_IMAGE")
        ]
    else: # grpc
        client = grpcclient.InferenceServerClient(url="localhost:8001")
        inputs = [grpcclient.InferInput("IMAGE", img_batch.shape, "UINT8")]
        outputs = [
            grpcclient.InferRequestedOutput("JSON_RESULT"),
            grpcclient.InferRequestedOutput("VISUALIZED_IMAGE")
        ]

    inputs[0].set_data_from_numpy(img_batch)

    print(f"\n🚀 เริ่มการทดสอบด้วย {protocol.upper()} ...")
    
    # 3. Warm-up (รันทิ้ง 5 รอบ)
    print("🔥 กำลัง Warm-up GPU...")
    for _ in range(5):
        client.infer(model_name=model_name, inputs=inputs, outputs=outputs, parameters=request_params)

    # 4. เริ่มจับเวลาจริง
    print(f"⏱️ กำลังรันทดสอบจำนวน {num_requests} รอบ...")
    latencies = []
    
    start_total_time = time.perf_counter()
    
    for i in range(num_requests):
        start_req_time = time.perf_counter()
        
        # ยิง Request
        client.infer(model_name=model_name, inputs=inputs, outputs=outputs, parameters=request_params)
        
        end_req_time = time.perf_counter()
        latencies.append((end_req_time - start_req_time) * 1000) # เก็บค่าเป็น ms

    end_total_time = time.perf_counter()

    # 5. สรุปผล
    total_time = end_total_time - start_total_time
    avg_latency = np.mean(latencies)
    p99_latency = np.percentile(latencies, 99)
    throughput = num_requests / total_time

    print("-" * 40)
    print(f"📊 ผลลัพธ์สำหรับ {protocol.upper()}")
    print("-" * 40)
    print(f"จำนวน Request ทั้งหมด : {num_requests} ครั้ง")
    print(f"เวลาที่ใช้รวม        : {total_time:.2f} วินาที")
    print(f"Throughput (FPS)     : {throughput:.2f} ภาพ/วินาที")
    print(f"Average Latency      : {avg_latency:.2f} ms")
    print(f"99th Percentile (P99): {p99_latency:.2f} ms")
    print("-" * 40)

if __name__ == "__main__":
    # รันเทสทั้ง 2 แบบต่อเนื่องกันเพื่อดูความต่าง
    run_benchmark(protocol="http", num_requests=50)
    run_benchmark(protocol="grpc", num_requests=50)