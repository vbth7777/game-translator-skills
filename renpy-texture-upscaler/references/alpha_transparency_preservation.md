# 4-Channel Alpha Transparency Preservation (Zero-Halo Dual-Plane Method)

## 1. The Alpha Transparency Problem in Game Textures

Video game character sprites, Live2D texture atlases, and UI elements heavily utilize transparent 32-bit RGBA PNG/WebP files.
When applying neural super-resolution models:
1. **Model Limitations**: Deep learning super-resolution architectures (Real-ESRGAN, SwinIR, ESRGAN) are trained strictly on 3-channel (RGB) images.
2. **Naive Resizing Flaws**:
   - *Dropping Alpha*: Turns transparent regions solid black or white, corrupting character cutouts.
   - *Bilinear Alpha Scaling*: Upscaling RGB with AI while scaling Alpha with bilinear interpolation produces a severe resolution mismatch at borders: sharp color lines combined with blurry alpha masks create **black halos**, **white borders**, or **fringe artifacts**.

---

## 2. The Dual-Plane Neural Solution

To ensure alpha boundaries possess the exact same subpixel vector sharpness and edge alignment as the color channels, we utilize the **Dual-Plane Neural Processing Architecture**:

```
                       [Input 32-bit RGBA Image]
                                  │
                 ┌────────────────┴────────────────┐
                 ▼                                 ▼
         [Plane 1: BGR]                    [Plane 2: Alpha]
      Shape: [H, W, 3]                  Shape: [H, W, 1]
      Normalized to [0.0, 1.0]          Replicate to 3 channels: [α, α, α]
                 │                                 │
                 ▼                                 ▼
         ┌───────────────┐                 ┌───────────────┐
         │ Real-ESRGAN   │                 │ Real-ESRGAN   │
         │ Neural Engine │                 │ Neural Engine │
         └───────┬───────┘                 └───────┬───────┘
                 │                                 │
                 ▼                                 ▼
      [Upscaled BGR Canvas]             [Upscaled Alpha Canvas]
      Shape: [H*4, W*4, 3]              Extract single channel: [H*4, W*4]
                 │                                 │
                 └────────────────┬────────────────┘
                                  ▼
                     [Merged 32-bit RGBA Output]
                     Shape: [H*4, W*4, 4]
                     Clean edges, Zero halo, Zero fringe!
```

---

## 3. Code Implementation

```python
# Extract Color and Alpha planes
bgr = img[:, :, :3].astype(np.float32) / 255.0
alpha = img[:, :, 3].astype(np.float32) / 255.0

# Replicate alpha to 3 channels for neural compatibility
alpha_3ch = np.stack([alpha, alpha, alpha], axis=2)

# Run neural inference through identical weights
out_bgr = neural_engine.process(bgr)
out_alpha_3ch = neural_engine.process(alpha_3ch)

# Extract neural alpha channel and clamp
out_alpha = out_alpha_3ch[:, :, 0]

# Merge into pristine 4-channel BGRA uint8 array
out_bgr_u8 = (np.clip(out_bgr, 0.0, 1.0) * 255.0).round().astype(np.uint8)
out_alpha_u8 = (np.clip(out_alpha, 0.0, 1.0) * 255.0).round().astype(np.uint8)

pristine_rgba = np.dstack([out_bgr_u8, out_alpha_u8])
```

