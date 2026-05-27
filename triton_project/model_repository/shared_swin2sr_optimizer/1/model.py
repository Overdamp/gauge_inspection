import cv2
import numpy as np
import triton_python_backend_utils as pb_utils

class TritonPythonModel:
    def initialize(self, args):
        self.logger = pb_utils.Logger
        self.logger.log_info("Initializing swin2sr BLS wrapper...")

    def execute(self, requests):
        responses = []
        for request in requests:
            in_image_tensor = pb_utils.get_input_tensor_by_name(request, "IMAGE")
            in_image = in_image_tensor.as_numpy()
            
            try:
                # Support both batched (4D) and unbatched (3D) inputs
                is_batched = (in_image.ndim == 4)
                if not is_batched:
                    images_list = [in_image]
                else:
                    images_list = [in_image[i] for i in range(in_image.shape[0])]
                
                out_images = []
                for img in images_list:
                    orig_h, orig_w = img.shape[:2]
                    
                    # Preprocess: RGB conversion, resize to static shape 64x64, normalize
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img_resized = cv2.resize(img_rgb, (64, 64), interpolation=cv2.INTER_CUBIC)
                    
                    # Normalize: rescale to [0, 1] and transpose to [3, H, W]
                    pixel_values = img_resized.astype(np.float32) / 255.0
                    pixel_values = np.transpose(pixel_values, (2, 0, 1))
                    pixel_values = np.expand_dims(pixel_values, axis=0) # [1, 3, 64, 64]
                    
                    # Call TensorRT backend model via BLS
                    input_tensors = [pb_utils.Tensor("pixel_values", pixel_values)]
                    infer_request = pb_utils.InferenceRequest(
                        model_name="shared_swin2sr_plan",
                        requested_output_names=["reconstruction"],
                        inputs=input_tensors
                    )
                    infer_response = infer_request.exec()
                    if infer_response.has_error():
                        raise pb_utils.TritonModelException(infer_response.error().message())
                        
                    reconstruction = pb_utils.get_output_tensor_by_name(infer_response, "reconstruction").as_numpy()
                    
                    # Postprocess: squeeze batch, transpose, clamp, scale, convert to BGR, resize to target double resolution
                    out_img = reconstruction[0] # [3, 128, 128]
                    out_img = np.clip(out_img, 0.0, 1.0)
                    out_img = np.transpose(out_img, (1, 2, 0)) * 255.0
                    out_img = out_img.astype(np.uint8)
                    out_img_bgr = cv2.cvtColor(out_img, cv2.COLOR_RGB2BGR)
                    
                    # Resize to match double the original input crop dimensions
                    out_resized = cv2.resize(out_img_bgr, (orig_w * 2, orig_h * 2), interpolation=cv2.INTER_CUBIC)
                    out_images.append(out_resized)
                
                if is_batched:
                    out_image = np.stack(out_images)
                else:
                    out_image = out_images[0]
                    
            except Exception as e:
                self.logger.log_error(f"Swin2SR BLS Inference failed: {e}")
                # Fallback to standard bicubic interpolation if something fails
                out_images = []
                for img in images_list:
                    orig_h, orig_w = img.shape[:2]
                    out_images.append(cv2.resize(img, (orig_w * 2, orig_h * 2), interpolation=cv2.INTER_CUBIC))
                
                if is_batched:
                    out_image = np.stack(out_images)
                else:
                    out_image = out_images[0]

            out_tensor = pb_utils.Tensor("IMAGE_SR", out_image)
            responses.append(pb_utils.InferenceResponse(output_tensors=[out_tensor]))

        return responses

    def finalize(self):
        pass
