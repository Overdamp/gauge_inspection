import numpy as np
import json
import cv2
import triton_python_backend_utils as pb_utils

class TritonPythonModel:
    def initialize(self, args):
        self.logger = pb_utils.Logger
        self.logger.log_info("Task Abnormality Router Initialized")

    def execute(self, requests):
        responses = []
        for request in requests:
            image_tensor = pb_utils.get_input_tensor_by_name(request, "IMAGE")
            img = image_tensor.as_numpy()
            if img.ndim == 4: img = img[0]
            
            results = {
                "object_condition": "ABNORMAL",
                "abnormality_type": "oil_leak",
                "severity": "HIGH",
                "confidence": 0.89,
                "message": "Task V1 Mock: Abnormality detection succeeded"
            }
            vis_img = img.copy()
            cv2.rectangle(vis_img, (100, 150), (350, 400), (0, 0, 255), 3)
            cv2.putText(vis_img, "MOCK OIL LEAK (HIGH RISK)", (110, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            _, buffer = cv2.imencode('.jpg', vis_img)
            img_bytes = buffer.tobytes()
            json_str = json.dumps(results)
            
            out_json = pb_utils.Tensor("JSON_RESULT", np.array([json_str], dtype=object))
            out_img = pb_utils.Tensor("VISUALIZED_IMAGE", np.array([img_bytes], dtype=object))
            responses.append(pb_utils.InferenceResponse(output_tensors=[out_json, out_img]))
        return responses

    def finalize(self):
        pass
