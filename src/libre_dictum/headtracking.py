from __future__ import annotations

import math
import threading
import time
from typing import Callable, Optional, Tuple, Dict

import cv2
import mediapipe as mp
import numpy as np

BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode

from .abs_math import abs_min, abs_add, abs_pow

class FaceRotationTracker:
    def __init__(
        self,
        model_path: str,
        callback: Callable[[float, float], None],
        camera_index: int = 0,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
        gesture_callback: Optional[Callable[[str], None]] = None,
        gesture_definitions: Optional[Dict[str, Dict[str, Dict[str, float]]]] = None,
    ):
        self.callback = callback
        self.gesture_callback = gesture_callback
        self.camera_index = camera_index
        self.model_path = model_path
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.offset_x = offset_x
        self.offset_y = offset_y

        self.gesture_definitions = gesture_definitions or {}
        
        # Track active states to enforce hysteresis loops
        self._gesture_states = {name: False for name in self.gesture_definitions}

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def _worker(self) -> None:
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
        if not cap.isOpened():
            self._running = False
            raise RuntimeError(f"Could not open camera index {self.camera_index}")

        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        cap.set(cv2.CAP_PROP_FPS, 60)

        options = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self.model_path),
            running_mode=RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
            output_facial_transformation_matrixes=True,
            output_face_blendshapes=True,
        )

        last_timestamp_ms = 0

        try:
            with FaceLandmarker.create_from_options(options) as landmarker:
                while self._running:
                    ok, frame_bgr = cap.read()
                    if not ok:
                        continue

                    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

                    timestamp_ms = int(time.monotonic() * 1000)
                    if timestamp_ms <= last_timestamp_ms:
                        timestamp_ms = last_timestamp_ms + 1
                    last_timestamp_ms = timestamp_ms

                    result = landmarker.detect_for_video(mp_image, timestamp_ms)
                    if not result.face_landmarks:
                        continue

                    yaw, pitch = self._extract_yaw_pitch(result)
                    self.callback(yaw - self.offset_x, pitch - self.offset_y)

                    if result.face_blendshapes and self.gesture_callback and self.gesture_definitions:
                        blendshapes = result.face_blendshapes[0]
                        categories = getattr(blendshapes, 'categories', blendshapes)
                        scores = {cat.category_name: cat.score for cat in categories}

                        for gesture_name, conditions in self.gesture_definitions.items():
                            was_active = self._gesture_states.get(gesture_name, False)
                            
                            if not was_active:
                                # Determine if activation thresholds are met across all assigned features
                                can_activate = True
                                for feature, limits in conditions.items():
                                    score = scores.get(feature, 0.0)
                                    if "min" in limits and score < limits["min"]:
                                        can_activate = False
                                        break
                                    if "max" in limits and score > limits["max"]:
                                        can_activate = False
                                        break
                                
                                if can_activate:
                                    self.gesture_callback(gesture_name)
                                    self._gesture_states[gesture_name] = True
                            
                            else:
                                # Determine if the gesture should release based on ANY feature crossing its release threshold
                                should_release = False
                                for feature, limits in conditions.items():
                                    score = scores.get(feature, 0.0)
                                    
                                    if "min" in limits:
                                        release_val = limits.get("release", limits["min"])
                                        if score <= release_val:
                                            should_release = True
                                            break
                                            
                                    if "max" in limits:
                                        release_val = limits.get("release", limits["max"])
                                        if score >= release_val:
                                            should_release = True
                                            break
                                            
                                if should_release:
                                    self._gesture_states[gesture_name] = False
                                    
        finally:
            cap.release()

    def _extract_yaw_pitch(self, result) -> Tuple[float, float]:
        if not result.facial_transformation_matrixes:
            return 0.0, 0.0

        m = np.array(result.facial_transformation_matrixes[0], dtype=np.float64).reshape(4, 4)
        R = m[:3, :3]

        forward = R @ np.array([0.0, 0.0, 1.0], dtype=np.float64)

        yaw = math.degrees(math.atan2(forward[0], forward[2]))
        pitch = math.degrees(math.atan2(-forward[1], math.hypot(forward[0], forward[2])))

        return yaw, pitch
