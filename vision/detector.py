"""
Live defect detector — wraps YOLOv8 for use in the inspection control loop.

Usage:
    detector = Detector()                   # loads best.pt or best.onnx
    result = detector.detect(frame_bgr)     # numpy HxWx3 BGR
    # result.boxes, result.class_id, result.label, result.confidence
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

ROOT = Path(__file__).parent.parent
DEFAULT_MODEL = ROOT / "runs" / "train" / "weights" / "best.pt"
ONNX_MODEL    = ROOT / "runs" / "train" / "weights" / "best.onnx"

CLASS_NAMES = {0: "good", 1: "defect_crack", 2: "defect_discolor"}
DEFECT_CLASSES = {1, 2}

# BGR colours for overlay
COLOURS = {
    0: (50,  200, 50),   # green  — good
    1: (50,  50,  220),  # red    — crack
    2: (50,  150, 220),  # orange — discolor
}


@dataclass
class Detection:
    class_id:   int
    label:      str
    confidence: float
    box_xyxy:   np.ndarray        # [x1, y1, x2, y2] in pixels
    is_defect:  bool = field(init=False)

    def __post_init__(self):
        self.is_defect = self.class_id in DEFECT_CLASSES

    @property
    def center(self) -> tuple[float, float]:
        return ((self.box_xyxy[0] + self.box_xyxy[2]) / 2,
                (self.box_xyxy[1] + self.box_xyxy[3]) / 2)


@dataclass
class DetectionResult:
    detections: list[Detection]
    latency_ms: float
    frame_annotated: Optional[np.ndarray] = None

    @property
    def defects(self) -> list[Detection]:
        return [d for d in self.detections if d.is_defect]

    @property
    def best_defect(self) -> Optional[Detection]:
        if not self.defects:
            return None
        return max(self.defects, key=lambda d: d.confidence)


class Detector:
    def __init__(self, model_path: Optional[Path] = None,
                 conf_threshold: float = 0.45,
                 imgsz: int = 480):
        from ultralytics import YOLO

        if model_path is None:
            # Prefer ONNX for faster CPU inference
            if ONNX_MODEL.exists():
                model_path = ONNX_MODEL
            elif DEFAULT_MODEL.exists():
                model_path = DEFAULT_MODEL
            else:
                raise FileNotFoundError(
                    f"No trained model found.\n"
                    f"Expected: {DEFAULT_MODEL} or {ONNX_MODEL}\n"
                    f"Run: python vision/train_yolo.py"
                )

        print(f"Loading detector from {model_path}")
        self._model = YOLO(str(model_path))
        self._conf  = conf_threshold
        self._imgsz = imgsz

    def detect(self, frame_bgr: np.ndarray,
               annotate: bool = True) -> DetectionResult:
        t0 = time.perf_counter()

        results = self._model.predict(
            source=frame_bgr,
            conf=self._conf,
            imgsz=self._imgsz,
            device="cpu",
            verbose=False,
        )
        latency = (time.perf_counter() - t0) * 1000

        detections: list[Detection] = []
        if results and results[0].boxes is not None:
            boxes = results[0].boxes
            for box in boxes:
                cid  = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy()
                detections.append(Detection(
                    class_id=cid,
                    label=CLASS_NAMES.get(cid, str(cid)),
                    confidence=conf,
                    box_xyxy=xyxy,
                ))

        annotated = None
        if annotate:
            annotated = self._draw(frame_bgr.copy(), detections, latency)

        return DetectionResult(detections, latency, annotated)

    def _draw(self, img: np.ndarray,
              detections: list[Detection],
              latency_ms: float) -> np.ndarray:
        for det in detections:
            x1, y1, x2, y2 = det.box_xyxy.astype(int)
            colour = COLOURS.get(det.class_id, (200, 200, 200))
            cv2.rectangle(img, (x1, y1), (x2, y2), colour, 2)
            label = f"{det.label} {det.confidence:.2f}"
            cv2.putText(img, label, (x1, y1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, colour, 1, cv2.LINE_AA)

        status = f"Defects: {sum(1 for d in detections if d.is_defect)} | {latency_ms:.0f}ms"
        cv2.putText(img, status, (8, img.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)
        return img
