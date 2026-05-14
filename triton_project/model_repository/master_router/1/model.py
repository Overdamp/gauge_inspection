import os
import sys
import json
import cv2
import numpy as np
import asyncio
import triton_python_backend_utils as pb_utils

sys.path.append("/home/luke/gauge_inspection")
from libs.analog_gauge import EllipseFitter, GaugeCalculator

# เพิ่ม NumpyEncoder ตรงนี้
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

class TritonPythonModel:
    def initialize(self, args):
        self.logger = pb_utils.Logger
        self.logger.log_info("Master Router Initialized")
        self.fitter = EllipseFitter()
        self.calculator = GaugeCalculator()

    async def execute(self, requests):
        responses = []
        for request in requests:
            image_tensor = pb_utils.get_input_tensor_by_name(request, "IMAGE")
            
            # Receive UINT8 tensor [1, H, W, 3] and squeeze batch dim
            img = image_tensor.as_numpy()
            if img.ndim == 4:
                img = img[0]  # [H, W, 3]
            
            # Read TASK_TYPE from request parameters (sent as HTTP parameter)
            try:
                params = request.parameters()
                task_type_param = params.get("TASK_TYPE", None)
                if task_type_param is not None:
                    task_type = task_type_param.string_param
                else:
                    task_type = "analog_gauge"
            except Exception:
                task_type = "analog_gauge"
            
            self.logger.log_info(f"Received task: {task_type}")

            results = {}
            vis_img = img.copy()

            if task_type == "analog_gauge":
                results, vis_img = await self._process_analog_gauge(img)
            else:
                results = {"error": f"Unknown task_type: {task_type}"}

            # Encode image to JPEG bytes to avoid size 0 error on gRPC
            _, buffer = cv2.imencode('.jpg', vis_img)
            img_bytes = buffer.tobytes()

            # แก้ไขบรรทัดนี้: เพิ่ม cls=NumpyEncoder
            json_str = json.dumps(results, cls=NumpyEncoder)
            
            out_json = pb_utils.Tensor("JSON_RESULT", np.array([json_str], dtype=object))
            out_img = pb_utils.Tensor("VISUALIZED_IMAGE", np.array([img_bytes], dtype=object))
            
            responses.append(pb_utils.InferenceResponse(output_tensors=[out_json, out_img]))

        return responses

    async def _process_analog_gauge(self, img):
        orig_h, orig_w = img.shape[:2]
        SEG_SIZE = 640

        # 1. Segmentation — resize เฉพาะตอนส่ง YOLO เพื่อเลี่ยงปัญหา Shared Memory (SHM) กับภาพขนาดใหญ่
        img_for_seg = cv2.resize(img, (SEG_SIZE, SEG_SIZE))
        self.logger.log_info(f"Sending to analog_seg, shape={img_for_seg.shape} (orig={img.shape})")
        
        seg_req = pb_utils.InferenceRequest(
            model_name="analog_seg",
            requested_output_names=["SEG_JSON"],
            inputs=[pb_utils.Tensor("IMAGE", img_for_seg)]
        )
        seg_res = await seg_req.async_exec()
        if seg_res.has_error():
            self.logger.log_error(f"analog_seg error: {seg_res.error().message()}")
            return {"error": "Segmentation failed"}, img
        
        seg_json_arr = pb_utils.get_output_tensor_by_name(seg_res, "SEG_JSON").as_numpy()
        
        if seg_json_arr.size == 0:
            self.logger.log_error("SEG_JSON tensor is empty!")
            return {"error": "Segmentation returned empty result"}, img
        
        segmentations = json.loads(seg_json_arr[0].decode('utf-8'))

        if not segmentations:
            return {"error": "No segmentations found"}, img

        # Scale พิกัดกลับมายังขนาดภาพ Original เพื่อให้การ Crop OCR และการคำนวณ Math แม่นยำที่สุด
        sx = orig_w / SEG_SIZE
        sy = orig_h / SEG_SIZE
        for seg in segmentations:
            if "mask" in seg and len(seg["mask"]) > 0:
                seg["mask"] = [[pt[0]*sx, pt[1]*sy] for pt in seg["mask"]]
            if "bbox" in seg and len(seg["bbox"]) == 4:
                bx1, by1, bx2, by2 = seg["bbox"]
                seg["bbox"] = [bx1*sx, by1*sy, bx2*sx, by2*sy]

        self.logger.log_info(f"Segmentation OK: {len(segmentations)} objects, scaled to {orig_w}x{orig_h}")

        # 2. Ellipse Fitting
        ellipse_result = self._get_component_ellipse(segmentations)

        # 3. OCR (Crop จากภาพ Original)
        ocr_results = await self._run_ocr_pipeline(img, segmentations)

        # 4. Gauge Reading (บนภาพ Original)
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
            # Reconstruct mask points into tuple format if needed, or just pass numpy array
            mask_np = np.array(seg["mask"])
            if len(mask_np) == 0: continue
            fd = self.fitter.fit(mask_np)
            if fd:
                r = seg.copy()
                r.update(fd)
                ellipse_results.append(r)
        return ellipse_results

    def _preprocess_for_ocr(self, crop_bgr):
        lab = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4)).apply(l)
        enhanced = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
        return cv2.filter2D(enhanced, -1, kernel)

    async def _run_ocr_pipeline(self, frame, segmentations):
        target_classes = ["max-value", "min-value", "unit", "scale_number"]
        filtered = [s for s in segmentations if s["class"] in target_classes]

        best_max, best_min, others = None, None, []
        for seg in filtered:
            if seg["class"] == "max-value":
                if best_max is None or seg["conf"] > best_max.get("conf",0): best_max = seg
            elif seg["class"] == "min-value":
                if best_min is None or seg["conf"] > best_min.get("conf",0): best_min = seg
            else:
                others.append(seg)

        final = others + [s for s in [best_max, best_min] if s]
        if not final: return []

        img_h, img_w = frame.shape[:2]
        crop_images_list = []
        seg_metadata_list = []

        for seg in final:
            mask_points = np.array(seg["mask"])
            mask_center = None
            if len(mask_points) > 0:
                M = np.mean(mask_points, axis=0)
                mask_center = (int(M[0]), int(M[1]))

            bbox = seg.get("bbox")
            if bbox and len(bbox) == 4:
                bx1, by1, bx2, by2 = map(int, bbox)
            else:
                x, y, w, h = cv2.boundingRect(mask_points)
                bx1, by1, bx2, by2 = x, y, x+w, y+h

            w_box, h_box = bx2 - bx1, by2 - by1
            pad_x = max(10, int(w_box * 0.30))
            pad_y = max(10, int(h_box * 0.30))
            x1 = max(0, bx1 - pad_x)
            y1 = max(0, by1 - pad_y)
            x2 = min(img_w, bx2 + pad_x)
            y2 = min(img_h, by2 + pad_y)

            crop_img = frame[y1:y2, x1:x2].copy()
            if crop_img.size == 0: continue
            crop_img = self._preprocess_for_ocr(crop_img)
            crop_img = cv2.resize(crop_img, (0, 0), fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
            
            crop_images_list.append(crop_img)
            seg_metadata_list.append({
                "class": seg["class"],
                "mask_center": mask_center
            })

        # Run Swin2SR & OCR for each crop concurrently using Triton BLS
        tasks = []
        for cimg in crop_images_list:
            tasks.append(self._async_sr_and_ocr(cimg))

        results = await asyncio.gather(*tasks)

        ocr_results = []
        for i, (text, conf) in enumerate(results):
            ocr_results.append({
                "class": seg_metadata_list[i]["class"],
                "text": text,
                "confidence": float(conf),
                "mask_center": seg_metadata_list[i]["mask_center"]
            })
            
        return ocr_results

    async def _async_sr_and_ocr(self, crop_img):
        # 1. Swin2SR
        sr_req = pb_utils.InferenceRequest(
            model_name="swin2sr",
            requested_output_names=["IMAGE_SR"],
            inputs=[pb_utils.Tensor("IMAGE", crop_img)]
        )
        sr_res = await sr_req.async_exec()
        if not sr_res.has_error():
            crop_img = pb_utils.get_output_tensor_by_name(sr_res, "IMAGE_SR").as_numpy()

        # 2. Doctr OCR
        ocr_req = pb_utils.InferenceRequest(
            model_name="doctr_ocr",
            requested_output_names=["TEXT_RESULT", "CONFIDENCE"],
            inputs=[pb_utils.Tensor("IMAGE", crop_img)]
        )
        ocr_res = await ocr_req.async_exec()
        if not ocr_res.has_error():
            text = pb_utils.get_output_tensor_by_name(ocr_res, "TEXT_RESULT").as_numpy()[0].decode('utf-8')
            conf = pb_utils.get_output_tensor_by_name(ocr_res, "CONFIDENCE").as_numpy()[0]
            return text, float(conf)
        return "", 0.0

    def _select_best_needle(self, needle_segs, center):
        if not needle_segs: return None
        if len(needle_segs) == 1: return needle_segs[0]

        best_seg, best_score = None, -1
        for seg in needle_segs:
            pts = np.array(seg["mask"])
            if len(pts) == 0: continue
            dists = np.sqrt((pts[:, 0]-center[0])**2 + (pts[:, 1]-center[1])**2)
            min_d, max_d = float(np.min(dists)), float(np.max(dists))
            score = max_d / (min_d + 1.0) * (0.5 + seg.get("conf", 0.5))
            if score > best_score:
                best_score = score
                best_seg = seg
        return best_seg

    def _detect_unit(self, ocr_results):
        for ocr in ocr_results:
            if ocr["class"] == "unit" and ocr["confidence"] > 0.5:
                clean = "".join(c for c in ocr["text"] if c.isalpha() or c in "°/%")
                if clean: return clean
        for ocr in ocr_results:
            if ocr["class"] in ["max-value", "min-value", "scale_number"]:
                alpha = "".join(c for c in ocr["text"] if c.isalpha())
                if len(alpha) >= 2: return alpha
        return ""

    def _get_gauge_reading(self, crop_img, segmentations, ellipse_result, ocr_results):
        if not ellipse_result: return {"error": "No ellipse found", "debug_img": crop_img}

        center, best_ellipse = None, None
        for cls_list in [["centre", "center"], ["gauge"]]:
            cands = [r for r in ellipse_result if r["class"] in cls_list]
            if cands:
                best = max(cands, key=lambda x: x.get("conf", 0))
                center, best_ellipse = best["center"], best
                break
        if center is None and ellipse_result:
            center, best_ellipse = ellipse_result[0]["center"], ellipse_result[0]
        if center is None: return {"error": "No center found", "debug_img": crop_img}

        needle_mask = []
        needle_cands = [s for s in segmentations if s["class"] == "needle"]
        if needle_cands:
            best_needle = self._select_best_needle(needle_cands, center)
            if best_needle:
                needle_mask = best_needle["mask"]

        unit = self._detect_unit(ocr_results)

        result = self.calculator.process_gauge(center, needle_mask, ocr_results, best_ellipse)
        
        # Cleanup
        if result and "_calibration_debug" in result:
            del result["_calibration_debug"]

        debug_img = self._draw_debug(crop_img, center, result, unit)

        if result:
            result["unit"] = unit
            result["debug_img"] = debug_img
            return result
            
        return {"error": "Gauge calculation failed", "debug_img": debug_img}

    def _draw_debug(self, crop_img, center, result, unit):
        W, H = 400, 400
        vis = cv2.resize(crop_img.copy(), (W, H))
        oh, ow = crop_img.shape[:2]
        sx, sy = W / ow, H / oh
        cx, cy = int(center[0]*sx), int(center[1]*sy)
        f = cv2.FONT_HERSHEY_SIMPLEX

        cv2.circle(vis, (cx, cy), 6, (0,0,255), -1)
        cv2.circle(vis, (cx, cy), 3, (255,255,255), -1)

        if result and "value" in result:
            nt = (int(result["needle_tip"][0]*sx), int(result["needle_tip"][1]*sy))
            cv2.line(vis, (cx, cy), nt, (0,0,255), 2)
            u = f" {unit}" if unit else ""
            txt = f"Read: {result['value']:.1f}{u}"
            (tw,th),_ = cv2.getTextSize(txt, f, 0.7, 2)
            p = (10, th+10)
            cv2.rectangle(vis, (p[0]-2,p[1]-th-5),(p[0]+tw+2,p[1]+3),(255,255,255),-1)
            r2 = result.get('r2_score', 0)
            clr = (0,150,0) if r2>=0.8 else (0,165,255) if r2>=0.5 else (0,0,255)
            cv2.putText(vis, txt, p, f, 0.7, clr, 2)
            
            # Add extra info: R2, pts, and direction (CW/CCW)
            slope = result.get("slope", 0)
            info = f"R2:{r2:.2f} | pts:{result.get('fit_points','?')} | {'CW' if slope > 0 else 'CCW'}"
            (dw, dh), _ = cv2.getTextSize(info, f, 0.45, 1)
            dp = (10, p[1] + dh + 10)
            cv2.rectangle(vis, (dp[0]-2, dp[1]-dh-5), (dp[0]+dw+2, dp[1]+3), (255,255,255), -1)
            cv2.putText(vis, info, dp, f, 0.45, (0,0,0), 1)
        else:
            cv2.putText(vis, "Calc Failed", (10, 30), f, 0.7, (0,0,255), 2)
        return vis

    def finalize(self):
        pass