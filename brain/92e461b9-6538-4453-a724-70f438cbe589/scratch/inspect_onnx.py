import onnxruntime as ort

model_path = "/home/luke/gauge_inspection/models/analog_gauge_model/segmentation/best_segment_v1.onnx"
session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])

print("--- INPUTS ---")
for input in session.get_inputs():
    print(f"Name: {input.name}, Shape: {input.shape}, Type: {input.type}")

print("--- OUTPUTS ---")
for output in session.get_outputs():
    print(f"Name: {output.name}, Shape: {output.shape}, Type: {output.type}")
