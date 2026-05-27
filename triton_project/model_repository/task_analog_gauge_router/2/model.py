import os
import sys
import json
import cv2
import numpy as np
import asyncio
import triton_python_backend_utils as pb_utils
import torch
from ultralytics.utils.nms import non_max_suppression
from ultralytics.utils.ops import process_mask, scale_boxes

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
        self.logger.log_info("Task Analog Gauge Router Version 2 Initialized")
        self.fitter = EllipseFitter()
        self.calculator = GaugeCalculator()

    async def execute(self, requests):
        responses = []
        for request in requests:
            image_tensor = pb_utils.get_input_tensor_by_name(request, "IMAGE")
            img = image_tensor.as_numpy()
            if img.ndim == 4: img = img[0]
            
            results, vis_img = {}, img.copy()
            results, vis_img = await self._process_analog_gauge(img)
            
            _, buffer = cv2.imencode('.jpg', vis_img)
            img_bytes = buffer.tobytes()
            json_str = json.dumps(results, cls=NumpyEncoder)
            
            out_json = pb_utils.Tensor("JSON_RESULT", np.array([json_str], dtype=object))
            out_img = pb_utils.Tensor("VISUALIZED_IMAGE", np.array([img_bytes], dtype=object))
            responses.append(pb_utils.InferenceResponse(output_tensors=[out_json, out_img]))
        return responses

    def _letterbox(self, img, new_shape=(640, 640), color=(114, 114, 114)):
        shape = img.shape[:2]
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
        dw /= 2
        dh /= 2
        if shape[::-1] != new_unpad:
            img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
        return img, r, (dw, dh)

    async def _process_analog_gauge(self, img):
        self.logger.log_info(f"Analog Gauge Router V2: Sending Original Image to shared_analog_seg ONNX V2, shape={img.shape}")
        
        oh, ow = img.shape[:2]
        
        # Preprocessing: letterbox resize to 640x640, BGR to RGB, normalize, transpose to [1, 3, 640, 640]
        img_lb, r, (dw, dh) = self._letterbox(img, (640, 640))
        img_rgb = img_lb[:, :, ::-1] # BGR to RGB
        img_float = img_rgb.astype(np.float32) / 255.0
        img_transposed = np.transpose(img_float, (2, 0, 1)) # [3, 640, 640]
        img_batch = np.expand_dims(img_transposed, axis=0) # [1, 3, 640, 640]
        
        seg_req = pb_utils.InferenceRequest(
            model_name="shared_analog_seg",
            model_version=2,
            requested_output_names=["output0", "output1"],
            inputs=[pb_utils.Tensor("images", img_batch)]
        )
        seg_res = await seg_req.async_exec()
        if seg_res.has_error():
            self.logger.log_error(f"shared_analog_seg error: {seg_res.error().message()}")
            return {"error": "Segmentation failed"}, img
        
        output0_pb = pb_utils.get_output_tensor_by_name(seg_res, "output0")
        output1_pb = pb_utils.get_output_tensor_by_name(seg_res, "output1")

        pred = torch.from_dlpack(output0_pb.to_dlpack())
        proto = torch.from_dlpack(output1_pb.to_dlpack())

        # Run NMS
        nms_results = non_max_suppression(pred, conf_thres=0.5, iou_thres=0.5, nc=7)
        det = nms_results[0]

        segmentations = []
        class_names = {0: 'centre', 1: 'gauge', 2: 'max-value', 3: 'min-value', 4: 'needle', 5: 'scale_number', 6: 'unit'}

        if len(det) > 0:
            bboxes = det[:, :4]
            confs = det[:, 4]
            clss = det[:, 5]
            masks_coeffs = det[:, 6:]

            # Process masks at 640x640 on GPU
            masks = process_mask(proto[0], masks_coeffs, bboxes, (640, 640), upsample=True) # [N, 640, 640]

            # Scale boxes and move all required tensors to CPU once
            masks_cpu = (masks > 0.5).cpu().numpy().astype(np.uint8)
            bboxes_cpu = bboxes.cpu().numpy()
            clss_cpu = clss.cpu().numpy()
            confs_cpu = confs.cpu().numpy()

            for i in range(len(det)):
                c_id = int(clss_cpu[i])
                label = class_names.get(c_id, 'unknown')
                conf = float(confs_cpu[i])
                
                # Scale bbox back to original image space
                bx1, by1, bx2, by2 = bboxes_cpu[i]
                x1 = np.clip((bx1 - dw) / r, 0, ow - 1)
                y1 = np.clip((by1 - dh) / r, 0, oh - 1)
                x2 = np.clip((bx2 - dw) / r, 0, ow - 1)
                y2 = np.clip((by2 - dh) / r, 0, oh - 1)
                bbox = [float(x1), float(y1), float(x2), float(y2)]

                # Find contours on 640x640 mask directly and scale coordinates to original image size
                mask_bin = masks_cpu[i]
                contours, _ = cv2.findContours(mask_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    largest_contour = max(contours, key=cv2.contourArea)
                    pts = largest_contour.reshape(-1, 2)
                    pts_orig = (pts - np.array([dw, dh])) / r
                    pts_orig[:, 0] = np.clip(pts_orig[:, 0], 0, ow - 1)
                    pts_orig[:, 1] = np.clip(pts_orig[:, 1], 0, oh - 1)
                    polygon_pts = pts_orig.astype(int).tolist()
                else:
                    polygon_pts = []

                segmentations.append({
                    "class": label,
                    "conf": conf,
                    "bbox": bbox,
                    "mask": polygon_pts
                })

        if not segmentations:
            return {"error": "No segmentations found"}, img

        self.logger.log_info(f"Analog Gauge Router: Received {len(segmentations)} objects in original space.")

        segs_summary = [{"class": s["class"], "conf": s["conf"], "bbox": s["bbox"]} for s in segmentations]
        self.logger.log_info(f"DEBUG: segmentations_summary={segs_summary}")
        ellipse_result = self._get_component_ellipse(segmentations)
        ocr_results = await self._run_ocr_pipeline(img, segmentations)
        self.logger.log_info(f"DEBUG: ocr_results={ocr_results}")
        result_dict = self._get_gauge_reading(img, segmentations, ellipse_result, ocr_results)
        
        # Save debug JSON for analysis
        try:
            import os
            os.makedirs("/home/luke/gauge_inspection/debug_output", exist_ok=True)
            with open("/home/luke/gauge_inspection/debug_output/debug_triton_ag5.json", "w") as f:
                json.dump({
                    "segmentations": [{k: v for k, v in s.items() if k != "mask"} for s in segmentations],
                    "ocr_results": ocr_results,
                    "ellipse_result": [{k: v for k, v in e.items() if k != "mask"} for e in ellipse_result],
                    "result_dict": {k: v for k, v in result_dict.items() if k != "debug_img"}
                }, f, indent=2, cls=NumpyEncoder)
            with open("/home/luke/gauge_inspection/debug_output/debug_triton_ag5_full.json", "w") as f:
                json.dump({
                    "segmentations": segmentations,
                    "ocr_results": ocr_results,
                    "ellipse_result": ellipse_result,
                    "result_dict": {k: v for k, v in result_dict.items() if k != "debug_img"}
                }, f, indent=2, cls=NumpyEncoder)
        except Exception as e:
            self.logger.log_error(f"Failed to save debug JSON: {e}")
            
        vis_img = result_dict.pop("debug_img", img)
        return result_dict, vis_img

    def _get_component_ellipse(self, segmentation):
        # Match original priority order to get exactly the same pivot center and perspective parameters:
        # Priority 1: centre / center
        for seg in segmentation:
            if seg["class"] in ["centre", "center"]:
                mask_np = np.array(seg["mask"])
                if len(mask_np) >= 5:
                    fd = self.fitter.fit(mask_np)
                    if fd:
                        r = seg.copy(); r.update(fd)
                        return [r]
                        
        # Priority 2: gauge
        for seg in segmentation:
            if seg["class"] == "gauge":
                mask_np = np.array(seg["mask"])
                if len(mask_np) >= 5:
                    fd = self.fitter.fit(mask_np)
                    if fd:
                        r = seg.copy(); r.update(fd)
                        return [r]
                        
        # Priority 3: other components except unit, needle, max-value, min-value
        for seg in segmentation:
            if seg["class"] not in ["unit", "needle", "max-value", "min-value", "centre", "center", "gauge"]:
                mask_np = np.array(seg["mask"])
                if len(mask_np) >= 5:
                    fd = self.fitter.fit(mask_np)
                    if fd:
                        r = seg.copy(); r.update(fd)
                        return [r]
                        
        # Priority 4: max-value, min-value (best_max, best_min)
        best_max = None
        best_min = None
        for seg in segmentation:
            if seg["class"] == "max-value":
                if best_max is None or seg["conf"] > best_max["conf"]: best_max = seg
            elif seg["class"] == "min-value":
                if best_min is None or seg["conf"] > best_min["conf"]: best_min = seg
        for seg in [s for s in [best_max, best_min] if s]:
            mask_np = np.array(seg["mask"])
            if len(mask_np) >= 5:
                fd = self.fitter.fit(mask_np)
                if fd:
                    r = seg.copy(); r.update(fd)
                    return [r]
                    
        return []

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

        async def process_single_crop(seg):
            mask_points = np.array(seg["mask"])
            mask_center = None
            if len(mask_points) > 0:
                M = cv2.moments(mask_points.astype(np.float32))
                if M["m00"] != 0:
                    mask_center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                else:
                    mask_center = (int(np.mean(mask_points[:, 0])), int(np.mean(mask_points[:, 1])))

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
            if crop_img.size == 0: return None
            crop_img = self._preprocess_for_ocr(crop_img)
            crop_resized = cv2.resize(crop_img, (0, 0), fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)

            # Swin2SR
            processed_crop = crop_resized
            sr_req = pb_utils.InferenceRequest(
                model_name="shared_swin2sr_optimizer",
                requested_output_names=["IMAGE_SR"],
                inputs=[pb_utils.Tensor("IMAGE", np.expand_dims(crop_resized, axis=0))]
            )
            sr_res = await sr_req.async_exec()
            if not sr_res.has_error():
                processed_crop = pb_utils.get_output_tensor_by_name(sr_res, "IMAGE_SR").as_numpy()[0]
            else:
                self.logger.log_error(f"shared_swin2sr_optimizer error: {sr_res.error().message()}")
                processed_crop = cv2.resize(crop_img, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

            # DocTR OCR
            ocr_req = pb_utils.InferenceRequest(
                model_name="shared_doctr_ocr",
                requested_output_names=["TEXT_RESULT", "CONFIDENCE"],
                inputs=[pb_utils.Tensor("IMAGE", np.expand_dims(processed_crop, axis=0))]
            )
            ocr_res = await ocr_req.async_exec()
            text, conf = "", 0.0
            if not ocr_res.has_error():
                t = pb_utils.get_output_tensor_by_name(ocr_res, "TEXT_RESULT").as_numpy()[0][0]
                text = t.decode('utf-8') if isinstance(t, bytes) else str(t)
                conf = float(pb_utils.get_output_tensor_by_name(ocr_res, "CONFIDENCE").as_numpy()[0][0])
            else:
                self.logger.log_error(f"shared_doctr_ocr error: {ocr_res.error().message()}")

            return {
                "class": seg["class"],
                "text": text,
                "confidence": conf,
                "mask_center": mask_center
            }

        results = []
        for seg in final:
            res = await process_single_crop(seg)
            if res is not None:
                results.append(res)
        return results

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
        self.logger.log_info(f"DEBUG: center={center}, class={ellipse_result[0].get('class')}")
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
