import numpy as np
import json
import triton_python_backend_utils as pb_utils

class TritonPythonModel:
    def initialize(self, args):
        self.logger = pb_utils.Logger
        self.logger.log_info("Initializing util_level_calculator...")

    def execute(self, requests):
        responses = []
        for request in requests:
            in_data = pb_utils.get_input_tensor_by_name(request, "INPUT_DATA").as_numpy()
            res_dict = {
                "calculated_level_pct": 75.4,
                "status": "success"
            }
            out_str = np.array([json.dumps(res_dict)], dtype=np.object_)
            out_tensor = pb_utils.Tensor("OUTPUT_DATA", out_str)
            responses.append(pb_utils.InferenceResponse(output_tensors=[out_tensor]))

        return responses

    def finalize(self):
        pass
