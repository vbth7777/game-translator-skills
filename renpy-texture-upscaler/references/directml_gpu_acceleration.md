# DirectML GPU Acceleration & Tiled Inference Architecture

## 1. Why DirectML Over Native PyTorch CUDA on Windows

In Windows game engineering environments:
- Standard `pip install torch` frequently defaults to the CPU wheel, or fails to detect GPU drivers due to CUDA version mismatches (e.g. CUDA 11.8 vs 12.x vs 13.x).
- Installing CUDA toolkits requires downloading 3–5 GB of dependencies and administrator privileges.

### The DirectML Advantage:
- **`onnxruntime-directml`** communicates directly with Microsoft DirectX 12 (`d3d12.dll`).
- Taps 100% of GPU compute (NVIDIA GeForce RTX, AMD Radeon RX, Intel Arc) immediately.
- Execution speed matches or exceeds native PyTorch CUDA while maintaining low VRAM overhead.

---

## 2. Exporting Real-ESRGAN to Dynamic ONNX

To support textures of arbitrary aspect ratios (e.g., $1024 \times 1024$, $1024 \times 2048$, $512 \times 1024$), the model must be exported with **dynamic axes**:

```python
import torch
from basicsr.archs.rrdbnet_arch import RRDBNet

model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4)
state_dict = torch.load('RealESRGAN_x4plus_anime_6B.pth', map_location='cpu')
keyname = 'params_ema' if 'params_ema' in state_dict else 'params'
model.load_state_dict(state_dict[keyname], strict=True)
model.eval()

dummy_input = torch.randn(1, 3, 256, 256)
torch.onnx.export(
    model,
    dummy_input,
    'realesrgan_anime_6b.onnx',
    input_names=['input'],
    output_names=['output'],
    dynamic_axes={
        'input': {2: 'height', 3: 'width'},
        'output': {2: 'out_height', 3: 'out_width'}
    },
    opset_version=17
)
```

---

## 3. Tiled Inference Math (Eliminating VRAM OOM & Seams)

When processing large game atlases ($2048 \times 4096$ or $4096 \times 4096$), passing the entire image into GPU memory in a single tensor can cause an **Out of Memory (OOM)** error.

### Tiling with Border Padding:
To eliminate tile boundary seams:
1. Divide canvas into blocks of `step = 512` pixels.
2. Add an overlap margin of `pad = 16` pixels on all sides:
   $$y_0 = \max(0, y - \text{pad}), \quad y_1 = \min(H, y + \text{step} + \text{pad})$$
   $$x_0 = \max(0, x - \text{pad}), \quad x_1 = \min(W, x + \text{step} + \text{pad})$$
3. Feed the padded tile $[1, 3, y_1 - y_0, x_1 - x_0]$ into the ONNX session.
4. Discard the outer pad region from the upscaled prediction:
   $$\text{crop}_{y0} = (y - y_0) \times \text{scale}$$
   $$\text{crop}_{y1} = \text{crop}_{y0} + (\min(H, y + \text{step}) - y) \times \text{scale}$$
5. Place the cropped region into the master canvas.
6. **Result**: 100% continuous, seamless upscaling with flat VRAM usage under 1.5 GB.

