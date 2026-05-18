import numpy as np
import json
import triton_python_backend_utils as pb_utils

class TritonPythonModel:
    def initialize(self, args):
        self.logger = pb_utils.Logger
        self.logger.log_info("Initializing shared_gas_motion_detector...")

    def execute(self, requests):
        responses = []
        for request in requests:
            res_dict = {
                "gas_detected": True,
                "confidence": 0.92,
                "leak_area": [300, 400, 150, 150]
            }
            out_json = np.array([json.dumps(res_dict)], dtype=np.object_)
            out_tensor = pb_utils.Tensor("GAS_JSON", out_json)
            responses.append(pb_utils.InferenceResponse(output_tensors=[out_tensor]))

        return responses

    def finalize(self):
        pass
