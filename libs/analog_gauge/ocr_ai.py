import os
os.environ["LRU_CACHE_CAPACITY"] = "1"
os.environ["TORCH_CPP_LOG_LEVEL"] = "ERROR"

import cv2
import json
import numpy as np
import torch
from torchvision.transforms.v2 import Resize, Compose, ToImage, ToDtype
from doctr.models import recognition

class DoctrOCR:
    def __init__(self, model_dir: str, device: str = "cpu"):
        self.device = device
        self.model_dir = model_dir
        
        config_path = os.path.join(model_dir, "config.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config not found at {config_path}")
            
        with open(config_path, "r") as f:
            self.cfg = json.load(f)
            
        self.vocab = self.cfg.get("vocab")
        self.input_size = tuple(self.cfg.get("INPUT_SIZE", [32, 128]))
        self.model_arch = self.cfg.get("MODEL_ARCH", "parseq")
        
        self.model = recognition.__dict__[self.model_arch](
            pretrained=False, 
            vocab=self.vocab, 
            input_shape=(3, self.input_size[0], self.input_size[1])
        )
        
        ckpt_path = os.path.join(model_dir, "best_model.pt")
        if not os.path.exists(ckpt_path):
            raise FileNotFoundError(f"Checkpoint not found at {ckpt_path}")
            
        state_dict = torch.load(ckpt_path, map_location=self.device)
        if "model_state_dict" in state_dict:
            state_dict = state_dict["model_state_dict"]
            
        clean_state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}
        self.model.load_state_dict(clean_state_dict)
        self.model.to(self.device)
        self.model.eval()
        
        self.transforms = Compose([
            ToImage(),
            ToDtype(torch.float32, scale=True),
            Resize(self.input_size, antialias=True),
        ])

    def predict(self, img_bgr: np.ndarray):
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_tensor = self.transforms(img_rgb).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            output = self.model(img_tensor, target=None, return_preds=True)
            
        if "preds" in output:
            pred_text, conf = output['preds'][0]
        else:
            pred_text, conf = output[0]
            
        return pred_text, conf

    def predict_batch(self, images: list):
        if not images:
            return []
        
        tensors = []
        for img_bgr in images:
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            tensors.append(self.transforms(img_rgb))
            
        img_tensor = torch.stack(tensors).to(self.device)
        
        with torch.no_grad():
            output = self.model(img_tensor, target=None, return_preds=True)
            
        results = []
        preds = output['preds'] if 'preds' in output else output
        for i in range(len(images)):
            pred_text, conf = preds[i]
            results.append((pred_text, float(conf)))
            
        return results