import numpy as np
import json
import cv2
import triton_python_backend_utils as pb_utils

class TritonPythonModel:
    def initialize(self, args):
        self.logger = pb_utils.Logger
        self.logger.log_info("Task General Scan Router Initialized")

    def execute(self, requests):
        responses = []
        for request in requests:
            image_tensor = pb_utils.get_input_tensor_by_name(request, "IMAGE")
            img = image_tensor.as_numpy()
            if img.ndim == 4: img = img[0]
            
            results = {
                "fire_detected": False,
                "smoke_detected": True,
                "confidence": 0.87,
                "message": "Task V1 Mock: Fire/smoke safety scanning succeeded"
            }
            vis_img = img.copy()
            cv2.rectangle(vis_img, (150, 100), (450, 400), (200, 200, 200), 3)
            cv2.putText(vis_img, "MOCK SMOKE DETECTED", (160, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (128, 128, 128), 2)
            
            _, buffer = cv2.imencode('.jpg', vis_img)
            img_bytes = buffer.tobytes()
            json_str = json.dumps(results)
            
            out_json = pb_utils.Tensor("JSON_RESULT", np.array([json_str], dtype=object))
            out_img = pb_utils.Tensor("VISUALIZED_IMAGE", np.array([img_bytes], dtype=object))
            responses.append(pb_utils.InferenceResponse(output_tensors=[out_json, out_img]))
        return responses

    def finalize(self):
        pass
