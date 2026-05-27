import os
import json
import cv2
import numpy as np
import triton_python_backend_utils as pb_utils

class TritonPythonModel:
    def initialize(self, args):
        self.logger = pb_utils.Logger
        self.logger.log_info("Initializing doctr_ocr BLS wrapper...")
        
        # Load vocab and configuration
        model_dir = "/home/luke/gauge_inspection2/models/analog_gauge_model/ocr"
        config_path = os.path.join(model_dir, "config.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config not found at {config_path}")
            
        with open(config_path, "r") as f:
            self.cfg = json.load(f)
            
        self.vocab = self.cfg.get("vocab")
        self.input_size = tuple(self.cfg.get("INPUT_SIZE", [32, 128])) # [H, W]
        
        # Reconstruct embedding vocabulary list
        self._embedding = list(self.vocab) + ["<eos>", "<sos>", "<pad>"]
        self.logger.log_info(f"doctr_ocr wrapper initialized with vocab size {len(self.vocab)}")

    def execute(self, requests):
        responses = []
        for request in requests:
            in_image_tensor = pb_utils.get_input_tensor_by_name(request, "IMAGE")
            in_image = in_image_tensor.as_numpy()
            
            try:
                # Support batch and single image
                is_batched = (in_image.ndim == 4)
                if not is_batched:
                    images_list = [in_image]
                else:
                    images_list = [in_image[i] for i in range(in_image.shape[0])]
                
                texts = []
                confs = []
                
                for img in images_list:
                    # Preprocess: BGR -> RGB, resize to (W=128, H=32), normalized [0,1], CHW shape
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img_resized = cv2.resize(img_rgb, (self.input_size[1], self.input_size[0]), interpolation=cv2.INTER_LINEAR)
                    img_float = img_resized.astype(np.float32) / 255.0
                    img_transposed = np.transpose(img_float, (2, 0, 1))
                    img_input = np.expand_dims(img_transposed, axis=0) # [1, 3, 32, 128]
                    
                    # Call TensorRT model via BLS
                    input_tensors = [pb_utils.Tensor("input", img_input)]
                    infer_request = pb_utils.InferenceRequest(
                        model_name="shared_doctr_ocr_plan",
                        requested_output_names=["logits"],
                        inputs=input_tensors
                    )
                    infer_response = infer_request.exec()
                    if infer_response.has_error():
                        raise pb_utils.TritonModelException(infer_response.error().message())
                        
                    logits = pb_utils.get_output_tensor_by_name(infer_response, "logits").as_numpy() # [1, 33, 51]
                    
                    # Postprocess in NumPy
                    out_idxs = np.argmax(logits, axis=-1) # [1, 33]
                    
                    # Compute softmax probabilities: softmax = exp(x - max(x)) / sum(exp(x - max(x)))
                    shifted_logits = logits - np.max(logits, axis=-1, keepdims=True)
                    exp_logits = np.exp(shifted_logits)
                    probs_all = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)
                    preds_prob = np.max(probs_all, axis=-1) # [1, 33]
                    
                    # Decode to text and average confidence
                    encoded_seq = out_idxs[0]
                    word_chars = []
                    for idx in encoded_seq:
                        char = self._embedding[idx]
                        if char == "<eos>":
                            break
                        word_chars.append(char)
                    word = "".join(word_chars)
                    
                    if len(word) > 0:
                        word_prob = float(np.mean(np.clip(preds_prob[0, :len(word)], 0.0, 1.0)))
                    else:
                        word_prob = 0.0
                        
                    texts.append(word)
                    confs.append(word_prob)
                
                if is_batched:
                    text_tensor = pb_utils.Tensor("TEXT_RESULT", np.array([[t] for t in texts], dtype=object))
                    conf_tensor = pb_utils.Tensor("CONFIDENCE", np.array([[c] for c in confs], dtype=np.float32))
                else:
                    text_tensor = pb_utils.Tensor("TEXT_RESULT", np.array([texts[0]], dtype=object))
                    conf_tensor = pb_utils.Tensor("CONFIDENCE", np.array([confs[0]], dtype=np.float32))
                    
            except Exception as e:
                self.logger.log_error(f"DocTR OCR BLS Inference failed: {e}")
                if is_batched:
                    text_tensor = pb_utils.Tensor("TEXT_RESULT", np.array([[""] for _ in range(in_image.shape[0])], dtype=object))
                    conf_tensor = pb_utils.Tensor("CONFIDENCE", np.array([[0.0] for _ in range(in_image.shape[0])], dtype=np.float32))
                else:
                    text_tensor = pb_utils.Tensor("TEXT_RESULT", np.array([""], dtype=object))
                    conf_tensor = pb_utils.Tensor("CONFIDENCE", np.array([0.0], dtype=np.float32))

            responses.append(pb_utils.InferenceResponse(output_tensors=[text_tensor, conf_tensor]))

        return responses

    def finalize(self):
        pass
