# Live2D UV vs. Static 2D Screen Coords (The 2x Zoom Trap & SSAA Fix)

## 1. The Core Architectural Difference

When upscaling visual assets in the Ren'Py engine, assets fall into two fundamentally different rendering pipelines:

```
                          ┌────────────────────────┐
                          │   Ren'Py Image Asset   │
                          └───────────┬────────────┘
                                      │
                 ┌────────────────────┴────────────────────┐
                 ▼                                         ▼
   ┌───────────────────────────┐             ┌───────────────────────────┐
   │    Live2D Cubism Mesh     │             │    Static 2D Displayable  │
   │      (.moc3 + Atlas)      │             │  (Title, CG, Bust, UI)    │
   └─────────────┬─────────────┘             └─────────────┬─────────────┘
                 │                                         │
    Normalized UV Coords [0.0, 1.0]           Pixel Coordinates (1:1 Layout)
                 │                                         │
                 ▼                                         ▼
   SAFE TO UPSCALE DIRECTLY (4K)              WILL ZOOM 2X & OVERFLOW SCREEN
   Model scale & position stay fixed!         Unless SSAA downsampled or zoomed!
```

---

## 2. Why Live2D Models Are Immune to the Zoom Bug

1. **Normalized Texture Coordinates**:
   - In Live2D Cubism (`.moc3`), each vertex of the character mesh is mapped to texture space using normalized coordinates $(u, v) \in [0.0, 1.0]$.
   - Whether the texture atlas is $512 \times 1024$, $1024 \times 1024$, or upscaled to $2048 \times 4096$, the vertex $(u, v) = (0.5, 0.5)$ always samples the exact center of the atlas.
2. **On-Screen Transform**:
   - The physical bounding box and size of the character on screen are governed strictly by the `.moc3` mesh coordinates and the Ren'Py displayable transform (e.g. `zoom 1.0` or matrix bounds).
   - **Result**: Upscaling a Live2D texture atlas from $1024 \times 1024$ to $4096 \times 4096$ delivers 4x higher pixel density inside the existing polygon mesh. The character never grows in size, shifts position, or clips off screen.

---

## 3. Why Static 2D Images Suffer from the "2x Zoom Bug"

1. **1:1 Native Pixel Mapping**:
   - In standard Ren'Py visual novels, a 1080p game initializes with `gui.init(1920, 1080)`.
   - When a statement like `scene bg title_d` or `show cg emma_1` is evaluated, Ren'Py renders the raster image at its native pixel dimensions: 1 pixel in the image file = 1 virtual pixel on screen.
2. **The 2x Zoom / Clipping Phenomenon**:
   - If an asset designed for $1920 \times 1080$ (such as `images/bg/title_d.png`) is upscaled 2x to $3840 \times 2160$ and replaced directly in the archive:
   - Ren'Py attempts to draw a $3840 \times 2160$ bitmap onto a $1920 \times 1080$ viewport.
   - **Visual Consequence**: The image appears 200% magnified, centering or top-left anchored, cutting off the right and bottom half of the image (e.g., logo text cut in half, character faces cropped out).

---

## 4. The Solution: Super-Sampled Anti-Aliasing (SSAA) Resampling

To gain all the benefits of AI super-resolution (denoising, vector-sharp edge reconstruction, removal of JPEG/PNG compression artifacts) without breaking the game's UI layout:

```
[Original 1080p Image] 
        │
        ▼ (AI Upscale 2x / 4x via Real-ESRGAN Anime 6B)
[Reconstructed Ultra-HD 4K Canvas] 
        │  * Neural edge sharpening & denoising applied
        ▼ (Downsample to 1920x1080 using cv2.INTER_LANCZOS4)
[SSAA Pristine 1080p Output] 
        │
        └──> Exactly (1920, 1080) in size
        └──> 100% Layout compatibility (Zero 2x Zoom Bug)
        └──> Crystal-clear vector lines & artifact-free gradients
```

### Mathematical Principle of Lanczos Resampling:
Lanczos filtering computes output pixel intensities using a sinc-based windowed kernel:
$$L(x) = \begin{cases} \text{sinc}(x) \cdot \text{sinc}(x / a) & \text{if } -a < x < a \\ 0 & \text{otherwise} \end{cases}$$
where $a = 4$ for Lanczos-4. Downsampling from an AI-denoised 4K canvas using Lanczos-4 retains the high-frequency edge enhancements of the neural network while ensuring 100% pixel layout parity.

---

## 5. The 1080p Resolution Threshold Guardrail (Preventing the SSAA "Rỗ" / Pixelation Trap)

### A. The Signal Processing Reality: Why Low-Res SSAA Fails
During research across game engines (Benchmark RPG Maker session `67fa5fe0-f3de-4b0a-a15c-5823adf81816` vs Ren'Py PAWGVERSE session `9dee8b12-0526-4f6b-b4cc-ccee0219a338`), a critical boundary condition was uncovered:

> [!CAUTION]
> **SSAA Downsampling is strictly bounded by the Nyquist-Shannon sampling theorem and the canvas pixel budget:**
> - When an AI super-resolution model reconstructs an image, it sharpens lineart into ultra-high-frequency, vector-thin edges (often $< 1.0$ pixel wide in relative coordinate space).
> - **In Low-Resolution Canvases ($< 1080p$, e.g., $816 \times 624$ or $720p$)**:
>   - There simply are **not enough physical pixels** across a character's eye, eyelash, or hair strands to represent a smooth subpixel transition gradient (anti-aliasing band).
>   - Lanczos downsampling forcibly clamps the high-contrast thin lines into single discrete pixels without soft transitional borders.
>   - **Visual Result**: Curved anime lines collapse into harsh 1-pixel staircases (aliased steps), completely ruining the illustration and making it look like a 16-bit retro pixelated game ("bị rỗ / vỡ nét").
> - **In High-Resolution Canvases ($\ge 1080p$, e.g., Full HD $1920 \times 1080$ or Bust $1920 \times 2511$)**:
>   - The pixel budget is 4x to 10x denser (2.07M to 4.8M pixels).
>   - Lanczos-4 generates smooth 2-to-4 pixel wide multi-shade gradient fringes around lines.
>   - **Visual Result**: Pristine, filmic, vector-sharp lines without a single jagged staircase pixel.

### B. Summary of the Dual Threshold Architecture:
```
                      [Target Static 2D Asset]
                                 │
                Is Native Resolution >= 1080p?
                                 │
                ┌────────────────┴────────────────┐
               YES                               NO (< 1080p)
                │                                 │
                ▼                                 ▼
       [SSAA Lanczos Mode]             [Guardrail Native 2x Mode]
  - AI 2x/4x Super-Resolution     - Keep Native 2x (No SSAA downscale)
  - Lanczos downsample to 1080p   - Zero pixelation staircasing (No "rỗ")
  - 100% layout fit (no 2x zoom)  - Use Ren'Py Transform(zoom=0.5) or
  - Pristine anti-aliasing        - Use renpy_hd_override.rpy
```

