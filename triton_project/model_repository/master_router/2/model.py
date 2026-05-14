import os
import sys
import json
import cv2
import numpy as np
import asyncio
import triton_python_backend_utils as pb_utils

sys.path.append("/home/luke/gauge_inspection")
from libs.analog_gauge import EllipseFitter, GaugeCalculator

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer): return int(obj)
        elif isinstance(obj, np.floating): return float(obj)
        elif isinstance(obj, np.ndarray): return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

class TritonPythonModel:
    def initialize(self, args):
        self.logger = pb_utils.Logger
        self.logger.log_info("Master Router V2 (High Precision) Initialized")
        self.fitter = EllipseFitter()
        self.calculator = GaugeCalculator()

    async def execute(self, requests):
        responses = []
        for request in requests:
            image_tensor = pb_utils.get_input_tensor_by_name(request, "IMAGE")
            img = image_tensor.as_numpy()
            if img.ndim == 4: img = img[0]
            
            try:
                params = request.parameters()
                task_type_param = params.get("TASK_TYPE", None)
                task_type = task_type_param.string_param if task_type_param else "analog_gauge"
            except Exception:
                task_type = "analog_gauge"
            
            results, vis_img = {}, img.copy()
            if task_type == "analog_gauge":
                results, vis_img = await self._process_analog_gauge(img)
            else:
                results = {"error": f"Unknown task_type: {task_type}"}

            _, buffer = cv2.imencode('.jpg', vis_img)
            img_bytes = buffer.tobytes()
            json_str = json.dumps(results, cls=NumpyEncoder)
            
            out_json = pb_utils.Tensor("JSON_RESULT", np.array([json_str], dtype=object))
            out_img = pb_utils.Tensor("VISUALIZED_IMAGE", np.array([img_bytes], dtype=object))
            responses.append(pb_utils.InferenceResponse(output_tensors=[out_json, out_img]))
        return responses

    async def _process_analog_gauge(self, img):
        # V2 High Precision: ส่งภาพ Original ไปเลยเพื่อให้ YOLOv8 (retina_masks=True) คืนพิกัดที่ละเอียดที่สุด
        # ไม่ใช้การ Resize ใน master_router เพื่อเลี่ยงความคลาดเคลื่อนจากการ Upscale
        self.logger.log_info(f"V2 High Precision: Sending Original Image to analog_seg, shape={img.shape}")
        
        seg_req = pb_utils.InferenceRequest(
            model_name="analog_seg",
            requested_output_names=["SEG_JSON"],
            inputs=[pb_utils.Tensor("IMAGE", img)]
        )
        seg_res = await seg_req.async_exec()
        if seg_res.has_error():
            self.logger.log_error(f"analog_seg error: {seg_res.error().message()}")
            return {"error": "Segmentation failed"}, img
        
        seg_json_arr = pb_utils.get_output_tensor_by_name(seg_res, "SEG_JSON").as_numpy()
        segmentations = json.loads(seg_json_arr[0].decode('utf-8')) if seg_json_arr.size > 0 else []

        if not segmentations:
            return {"error": "No segmentations found"}, img

        # พิกัดที่ได้จะเป็น Original Space อยู่แล้ว เพราะ retina_masks=True ทำงานบนภาพต้นฉบับ
        self.logger.log_info(f"V2 High Precision: Received {len(segmentations)} objects in original space.")

        ellipse_result = self._get_component_ellipse(segmentations)
        ocr_results = await self._run_ocr_pipeline(img, segmentations)
        result_dict = self._get_gauge_reading(img, segmentations, ellipse_result, ocr_results)
        
        vis_img = result_dict.pop("debug_img", img)
        return result_dict, vis_img

    def _get_component_ellipse(self, segmentation):
        ellipse_results = []
        best_max, best_min, other = None, None, []
        for seg in segmentation:
            c = seg["class"]
            if c == "max-value":
                if best_max is None or seg["conf"] > best_max.get("conf", 0): best_max = seg
            elif c == "min-value":
                if best_min is None or seg["conf"] > best_min.get("conf", 0): best_min = seg
            elif c not in ["unit", "needle"]:
                other.append(seg)
        
        final_segs = other + [s for s in [best_max, best_min] if s]
        for seg in final_segs:
            mask_np = np.array(seg["mask"])
            if len(mask_np) < 5: continue
            fd = self.fitter.fit(mask_np)
            if fd:
                r = seg.copy(); r.update(fd); ellipse_results.append(r)
        return ellipse_results

    def _preprocess_for_ocr(self, crop_bgr):
        lab = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab); l = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4)).apply(l)
        enhanced = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
        return cv2.filter2D(enhanced, -1, kernel)

    async def _run_ocr_pipeline(self, frame, segmentations):
        target_classes = ["max-value", "min-value", "unit", "scale_number"]
        filtered = [s for s in segmentations if s["class"] in target_classes]
        best_max, best_min, others = None, None, []
        for seg in filtered:
            if seg["class"] == "max-value":
                if best_max is None or seg["conf"] > seg.get("conf", 0): best_max = seg
            elif seg["class"] == "min-value":
                if best_min is None or seg["conf"] > seg.get("conf", 0): best_min = seg
            else: others.append(seg)
        final = others + [s for s in [best_max, best_min] if s]
        if not final: return []

        img_h, img_w = frame.shape[:2]
        crop_images_list, seg_metadata_list = [], []
        for seg in final:
            mask_points = np.array(seg["mask"])
            mask_center = (int(np.mean(mask_points[:, 0])), int(np.mean(mask_points[:, 1]))) if len(mask_points) > 0 else None
            bbox = seg.get("bbox")
            if bbox and len(bbox) == 4:
                bx1, by1, bx2, by2 = map(int, bbox)
            else:
                x, y, w, h = cv2.boundingRect(mask_points.astype(np.float32))
                bx1, by1, bx2, by2 = x, y, x+w, y+h
            
            w_box, h_box = bx2 - bx1, by2 - by1
            pad_x, pad_y = max(10, int(w_box * 0.3)), max(10, int(h_box * 0.3))
            x1, y1, x2, y2 = max(0, bx1-pad_x), max(0, by1-pad_y), min(img_w, bx2+pad_x), min(img_h, by2+pad_y)
            
            crop_img = frame[y1:y2, x1:x2].copy()
            if crop_img.size == 0: continue
            crop_img = self._preprocess_for_ocr(crop_img)
            
            # บังคับ Resize เป็น 32x128 สำหรับ Batch OCR
            crop_img = cv2.resize(crop_img, (128, 32), interpolation=cv2.INTER_CUBIC)
            
            crop_images_list.append(crop_img)
            seg_metadata_list.append({"class": seg["class"], "mask_center": mask_center})

        if not crop_images_list: return []

        # 🚀 ส่งไปทำ OCR แบบ Batch รวดเดียว (ข้าม Swin2SR เพื่อความเร็ว)
        batch_tensor = np.stack(crop_images_list).astype(np.uint8)
        ocr_req = pb_utils.InferenceRequest(
            model_name="doctr_ocr", 
            requested_output_names=["TEXT_RESULT", "CONFIDENCE"], 
            inputs=[pb_utils.Tensor("IMAGE", batch_tensor)]
        )
        ocr_res = await ocr_req.async_exec()
        
        ocr_results = []
        if not ocr_res.has_error():
            texts = pb_utils.get_output_tensor_by_name(ocr_res, "TEXT_RESULT").as_numpy()
            confs = pb_utils.get_output_tensor_by_name(ocr_res, "CONFIDENCE").as_numpy()
            for i in range(len(texts)):
                ocr_results.append({
                    "class": seg_metadata_list[i]["class"],
                    "text": texts[i].decode('utf-8'),
                    "confidence": float(confs[i]),
                    "mask_center": seg_metadata_list[i]["mask_center"]
                })
        return ocr_results

    def _select_best_needle(self, needle_segs, center):
        if not needle_segs: return None
        best_seg, best_score = None, -1
        for seg in needle_segs:
            pts = np.array(seg["mask"])
            if len(pts) == 0: continue
            dists = np.sqrt((pts[:, 0]-center[0])**2 + (pts[:, 1]-center[1])**2)
            min_d, max_d = float(np.min(dists)), float(np.max(dists))
            score = max_d / (min_d + 1.0) * (0.5 + seg.get("conf", 0.5))
            if score > best_score: best_score, best_seg = score, seg
        return best_seg

    def _detect_unit(self, ocr_results):
        for ocr in ocr_results:
            if ocr["class"] == "unit" and ocr["confidence"] > 0.5:
                clean = "".join(c for c in ocr["text"] if c.isalpha() or c in "°/%")
                if clean: return clean
        return ""

    def _get_gauge_reading(self, crop_img, segmentations, ellipse_result, ocr_results):
        if not ellipse_result: return {"error": "No ellipse", "debug_img": crop_img}
        center = ellipse_result[0]["center"]
        needle_mask = []
        needle_cands = [s for s in segmentations if s["class"] == "needle"]
        best_needle = self._select_best_needle(needle_cands, center)
        if best_needle: needle_mask = best_needle["mask"]
        unit = self._detect_unit(ocr_results)
        result = self.calculator.process_gauge(center, needle_mask, ocr_results, ellipse_result[0])
        if result and "_calibration_debug" in result: del result["_calibration_debug"]
        debug_img = self._draw_debug(crop_img, center, result, unit)
        if result:
            result.update({"unit": unit, "debug_img": debug_img})
            return result
        return {"error": "Calc failed", "debug_img": debug_img}

    def _draw_debug(self, crop_img, center, result, unit):
        W, H = 640, 640
        vis = cv2.resize(crop_img.copy(), (W, H))
        oh, ow = crop_img.shape[:2]
        sx, sy = W / ow, H / oh
        cx, cy = int(center[0]*sx), int(center[1]*sy)
        f = cv2.FONT_HERSHEY_SIMPLEX
        cv2.circle(vis, (cx, cy), 8, (0,0,255), -1)
        if result and "value" in result:
            nt = (int(result["needle_tip"][0]*sx), int(result["needle_tip"][1]*sy))
            cv2.line(vis, (cx, cy), nt, (0,0,255), 3)
            txt = f"Read: {result['value']:.2f} {unit}"
            cv2.putText(vis, txt, (20, 50), f, 1.0, (0,150,0), 3)
            info = f"R2:{result.get('r2_score',0):.2f} | pts:{result.get('fit_points','?')}"
            cv2.putText(vis, info, (20, 90), f, 0.6, (0,0,0), 2)
        return vis

    def finalize(self):
        pass
