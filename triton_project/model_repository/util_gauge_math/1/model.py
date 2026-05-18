import numpy as np
import json
import triton_python_backend_utils as pb_utils

class TritonPythonModel:
    def initialize(self, args):
        self.logger = pb_utils.Logger
        self.logger.log_info("Initializing util_gauge_math...")

    def execute(self, requests):
        responses = []
        for request in requests:
            in_data = pb_utils.get_input_tensor_by_name(request, "INPUT_DATA").as_numpy()
            # Simple echo or stub calculation
            res_dict = {
                "angle": 135.0,
                "reading": 1405.02,
                "status": "success"
            }
            out_str = np.array([json.dumps(res_dict)], dtype=np.object_)
            out_tensor = pb_utils.Tensor("OUTPUT_DATA", out_str)
            responses.append(pb_utils.InferenceResponse(output_tensors=[out_tensor]))

        return responses

    def finalize(self):
        pass
