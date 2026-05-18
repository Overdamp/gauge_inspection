import numpy as np
import json
import cv2
import triton_python_backend_utils as pb_utils

class TritonPythonModel:
    def initialize(self, args):
        self.logger = pb_utils.Logger
        self.logger.log_info("Task Digital Gauge Router Initialized")

    def execute(self, requests):
        responses = []
        for request in requests:
            image_tensor = pb_utils.get_input_tensor_by_name(request, "IMAGE")
            img = image_tensor.as_numpy()
            if img.ndim == 4: img = img[0]
            
            results = {
                "value": 120.5,
                "unit": "psi",
                "confidence": 0.98,
                "gauge_level": "Normal",
                "message": "Task V1 Mock: Digital Gauge inference succeeded"
            }
            vis_img = img.copy()
            cv2.rectangle(vis_img, (50, 50), (250, 250), (0, 255, 0), 3)
            cv2.putText(vis_img, "MOCK DIGITAL GAUGE: 120.5 psi", (60, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            _, buffer = cv2.imencode('.jpg', vis_img)
            img_bytes = buffer.tobytes()
            json_str = json.dumps(results)
            
            out_json = pb_utils.Tensor("JSON_RESULT", np.array([json_str], dtype=object))
            out_img = pb_utils.Tensor("VISUALIZED_IMAGE", np.array([img_bytes], dtype=object))
            responses.append(pb_utils.InferenceResponse(output_tensors=[out_json, out_img]))
        return responses

    def finalize(self):
        pass
