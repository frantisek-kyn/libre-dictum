from __future__ import annotations

import math
import threading
import time
from typing import Callable, Optional, Tuple

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

    ):
        self.callback = callback
        self.camera_index = camera_index
        self.model_path = model_path
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._prev_yaw: Optional[float] = None
        self._prev_pitch: Optional[float] = None
        self.offset_x = offset_x
        self.offset_y = offset_y

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
    
    def _apply_rotation_transformation(self, yaw: float, pitch: float) -> Tuple[float, float]:
        if abs(yaw) < self.dead_angle_h:
            yaw = 0
        else:
            yaw = abs_add(yaw, -self.dead_angle_h)
        if abs(pitch) < self.dead_angle_v:
            pitch = 0
        else:
            pitch = abs_add(pitch, -self.dead_angle_v)
        yaw = abs_pow(yaw, self.speed_power) * self.speed_mult
        pitch = abs_pow(pitch, self.speed_power) * self.speed_mult
        yaw = abs_min(yaw, self.max_speed)
        pitch = abs_min(pitch, self.max_speed)
        return yaw, pitch


    def _worker(self) -> None:
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            self._running = False
            raise RuntimeError(f"Could not open camera index {self.camera_index}")

        options = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self.model_path),
            running_mode=RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
            output_facial_transformation_matrixes=True,
        )

        last_timestamp_ms = 0

        try:
            with FaceLandmarker.create_from_options(options) as landmarker:
                while self._running:
                    ok, frame_bgr = cap.read()
                    if not ok:
                        continue

                    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(
                        image_format=mp.ImageFormat.SRGB,
                        data=frame_rgb,
                    )

                    timestamp_ms = int(time.monotonic() * 1000)
                    if timestamp_ms <= last_timestamp_ms:
                        timestamp_ms = last_timestamp_ms + 1
                    last_timestamp_ms = timestamp_ms

                    result = landmarker.detect_for_video(mp_image, timestamp_ms)
                    if not result.face_landmarks:
                        continue

                    yaw, pitch = self._extract_yaw_pitch(result)
                    self.callback(yaw - self.offset_x, pitch - self.offset_y)
        finally:
            cap.release()

    def _extract_yaw_pitch(self, result) -> Tuple[float, float]:
        """
        Uses the facial transformation matrix, not Euler decomposition.
        This is much less prone to sign flips near side profiles.
        """
        if not result.facial_transformation_matrixes:
            return 0.0, 0.0

        m = np.array(result.facial_transformation_matrixes[0], dtype=np.float64).reshape(4, 4)
        R = m[:3, :3]

        # The matrix maps canonical face space to detected face space.
        # If yaw/pitch come out mirrored on your setup, use R.T instead of R.
        forward = R @ np.array([0.0, 0.0, 1.0], dtype=np.float64)

        # Yaw: left/right turn
        yaw = math.degrees(math.atan2(forward[0], forward[2]))

        # Pitch: up/down tilt
        pitch = math.degrees(math.atan2(-forward[1], math.hypot(forward[0], forward[2])))

        return yaw, pitch
