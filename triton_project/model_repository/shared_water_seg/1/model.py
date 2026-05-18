import numpy as np
import json
import triton_python_backend_utils as pb_utils

class TritonPythonModel:
    def initialize(self, args):
        self.logger = pb_utils.Logger
        self.logger.log_info("Initializing shared_water_seg...")

    def execute(self, requests):
        responses = []
        for request in requests:
            res_dict = {
                "water_level_pct": 75.4,
                "meniscus_y": 450,
                "confidence": 0.93
            }
            out_json = np.array([json.dumps(res_dict)], dtype=np.object_)
            out_tensor = pb_utils.Tensor("SEG_JSON", out_json)
            responses.append(pb_utils.InferenceResponse(output_tensors=[out_tensor]))

        return responses

    def finalize(self):
        pass
