#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DirectML & ONNX Runtime GPU Real-ESRGAN Upscaler Engine
Specialized for Ren'Py Game Textures & Live2D Models.

Features:
- Native Windows DirectML execution (NVIDIA RTX, AMD Radeon, Intel Arc).
- Dual-plane 4-channel Alpha transparency preservation (zero border fringing/halos).
- Tiled inference with seamless border padding to eliminate seam artifacts and prevent VRAM OOM.
- Subpixel Lanczos resampling (SSAA) for static UI/CG/Bust layout preservation.
"""

import os
import sys
import time
import math
import cv2
import numpy as np

try:
    import onnxruntime as ort
except ImportError:
    ort = None


class GPURealESRGAN:
    def __init__(self, onnx_model_path=None, device_id=0, tile_size=512, tile_pad=16, scale=4):
        self.tile_size = tile_size
        self.tile_pad = tile_pad
        self.scale = scale
        self.device_id = device_id
        self.onnx_model_path = onnx_model_path
        self.session = None
        self.active_provider = "None"

        if onnx_model_path and os.path.exists(onnx_model_path):
            self._init_session(onnx_model_path, device_id)
        else:
            print(f"[GPURealESRGAN] Warning: ONNX model path '{onnx_model_path}' not provided or not found.")

    def _init_session(self, model_path, device_id):
        if ort is None:
            raise RuntimeError("onnxruntime is not installed. Please install: pip install onnxruntime-directml")

        sess_opts = ort.SessionOptions()
        sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        available_providers = ort.get_available_providers()
        print(f"[GPURealESRGAN] Available ONNX providers: {available_providers}")

        providers = []
        provider_options = []

        if 'DmlExecutionProvider' in available_providers:
            providers.append('DmlExecutionProvider')
            provider_options.append({'device_id': device_id})
        elif 'CUDAExecutionProvider' in available_providers:
            providers.append('CUDAExecutionProvider')
            provider_options.append({'device_id': device_id})
        
        providers.append('CPUExecutionProvider')
        provider_options.append({})

        self.session = ort.InferenceSession(
            model_path,
            sess_options=sess_opts,
            providers=providers,
            provider_options=provider_options
        )
        self.active_provider = self.session.get_providers()[0]
        print(f"[GPURealESRGAN] Session initialized successfully! Active Provider: {self.active_provider}")

    def _process_plane(self, plane):
        """
        Processes a single 3-channel plane [H, W, 3] with values in [0.0, 1.0].
        Uses tiled execution with padding to prevent VRAM OOM and border distortion.
        """
        h, w, c = plane.shape
        out_h, out_w = h * self.scale, w * self.scale
        out = np.zeros((out_h, out_w, c), dtype=np.float32)

        step = self.tile_size
        pad = self.tile_pad

        for y in range(0, h, step):
            for x in range(0, w, step):
                # Calculate padded bounding box
                y0 = max(0, y - pad)
                y1 = min(h, y + step + pad)
                x0 = max(0, x - pad)
                x1 = min(w, x + step + pad)

                tile = plane[y0:y1, x0:x1, :]
                tile_h, tile_w = tile.shape[:2]

                # Shape to NCHW [1, 3, H, W]
                inp = np.transpose(tile, (2, 0, 1))[np.newaxis, :, :, :]
                
                # Execute inference
                pred = self.session.run(None, {'input': inp})[0]
                pred = np.transpose(pred[0], (1, 2, 0))  # [H*scale, W*scale, 3]

                # Calculate placement coords inside output canvas (cropping away outer pad)
                crop_y0 = (y - y0) * self.scale
                crop_y1 = crop_y0 + (min(h, y + step) - y) * self.scale
                crop_x0 = (x - x0) * self.scale
                crop_x1 = crop_x0 + (min(w, x + step) - x) * self.scale

                out_y0 = y * self.scale
                out_y1 = out_y0 + (crop_y1 - crop_y0)
                out_x0 = x * self.scale
                out_x1 = out_x0 + (crop_x1 - crop_x0)

                out[out_y0:out_y1, out_x0:out_x1] = pred[crop_y0:crop_y1, crop_x0:crop_x1]

        return np.clip(out, 0.0, 1.0)

    def enhance(self, img_bgr_or_bgra, outscale=None, target_size=None):
        """
        Upscales an image while strictly preserving 4-channel Alpha transparency.
        
        Args:
            img_bgr_or_bgra (np.ndarray): Image array loaded with cv2.IMREAD_UNCHANGED.
            outscale (float, optional): Custom scale factor (e.g., 2.0 or 4.0).
            target_size (tuple, optional): (width, height) to resample to via Lanczos (SSAA mode).
        
        Returns:
            np.ndarray: Upscaled / resampled image array.
        """
        if self.session is None:
            raise RuntimeError("Model session is not loaded. Call _init_session first.")

        h, w = img_bgr_or_bgra.shape[:2]
        is_rgba = (len(img_bgr_or_bgra.shape) > 2 and img_bgr_or_bgra.shape[2] == 4)

        if is_rgba:
            # Dual-plane 4-channel processing
            bgr = img_bgr_or_bgra[:, :, :3].astype(np.float32) / 255.0
            alpha = img_bgr_or_bgra[:, :, 3].astype(np.float32) / 255.0
            alpha_3ch = np.stack([alpha, alpha, alpha], axis=2)

            out_bgr = self._process_plane(bgr)
            out_alpha_3ch = self._process_plane(alpha_3ch)
            out_alpha = out_alpha_3ch[:, :, 0]

            out_bgr_u8 = (out_bgr * 255.0).round().astype(np.uint8)
            out_alpha_u8 = (out_alpha * 255.0).round().astype(np.uint8)

            merged = np.dstack([out_bgr_u8, out_alpha_u8])
        else:
            bgr = img_bgr_or_bgra.astype(np.float32) / 255.0
            out_bgr = self._process_plane(bgr)
            merged = (out_bgr * 255.0).round().astype(np.uint8)

        # Handle custom outscale or SSAA target size
        if target_size is not None:
            # Explicit SSAA target size (e.g. downsampling back to original 1920x1080)
            target_w, target_h = target_size
            if (merged.shape[1], merged.shape[0]) != (target_w, target_h):
                merged = cv2.resize(merged, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
        elif outscale is not None and outscale != self.scale:
            target_w = int(w * outscale)
            target_h = int(h * outscale)
            merged = cv2.resize(merged, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)

        return merged


if __name__ == '__main__':
    print("Testing GPURealESRGAN standalone...")
    # Quick sanity check
    test_img = np.zeros((128, 128, 4), dtype=np.uint8)
    test_img[:, :, 0] = 120 # B
    test_img[:, :, 1] = 200 # G
    test_img[:, :, 2] = 255 # R
    test_img[:, :, 3] = 255 # Alpha
    print("Test image created: shape =", test_img.shape)
