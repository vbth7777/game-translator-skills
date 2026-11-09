# The SSAA "Rỗ" / Pixelation Trap in RPG Maker (Technical Post-Mortem)

## 1. The Catastrophic Failure of Low-Res SSAA (Session `67fa5fe0`)

In session `67fa5fe0-f3de-4b0a-a15c-5823adf81816`, the team attempted to upscale the illustrations and CGs of an RPG Maker MV game (`NTRPG Priestess`) using the standard Ren'Py approach:
1. Extract event CG `PriestxMermateNTR01.rpgmvp` (Native size: $816 \times 623$).
2. Run Real-ESRGAN Anime 6B to upscale 4x to $3264 \times 2496$.
3. Apply Lanczos-4 downsampling (SSAA) back to $816 \times 623$ to maintain exact in-game canvas layout.

### The Immediate Visual Disaster:
- When the user opened the game, character facial features, eyes, hair strands, and skin gradients were **harshly pixelated**, turning into **rough 1-pixel jagged staircases**.
- The user urgently reacted: *"mau dừng lại, upscale bị rỗ quá, kiểu thành pixel game luôn rồi!"* (Stop immediately, the upscale is way too grainy/jagged, it literally turned into a pixel game!).

---

## 2. Root Cause Analysis: Nyquist-Shannon Sampling & Pixel Density

Why does SSAA Lanczos downsampling work flawlessly in Ren'Py Full HD ($1920 \times 1080$), but completely destroy RPG Maker MV ($816 \times 624$)?

```
                       [AI Neural 4K Reconstruction]
                       Ultra-sharp vector-thin lines
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
       Ren'Py Canvas (1080p)                   RPG Maker MV (816x624)
  2,073,600 physical pixels                509,184 physical pixels (4x less!)
                 │                                       │
                 ▼                                       ▼
       [Lanczos Downsample]                    [Lanczos Downsample]
  Lines occupy 2 - 4 pixels                Lines are < 0.5 pixel wide!
  Sufficient space for smooth             Zero space for transitional shades!
  multi-shade anti-aliasing                Lanczos clamps to hard 1-pixel steps!
                 │                                       │
                 ▼                                       ▼
  🌟 Film-like, pristine smooth lines      💥 16-bit retro pixel staircasing ("rỗ")
```

### The Mathematics:
In a low-resolution canvas ($816 \times 624$), a fine line (such as an eyelash or hair strand) has a physical width smaller than 1 pixel. To appear smooth, an edge requires a transition gradient of 2 to 3 pixels of varying alpha/luminance (Anti-Aliasing). When forced into a discrete grid of 816 pixels without a high-DPI framebuffer, the transition pixels are rounded to binary values (0 or 255), creating severe aliased jaggedness.

---

## 3. The Definitive Architectural Solution: Native 2x + WebGL High-DPI Canvas

To eliminate pixelation and achieve true anime vector smoothness:

1. **NEVER downsample RPG Maker assets to $< 1080p$**:
   Keep the upscaled image at **Native 2x** ($1632 \times 1248$).
2. **Kích hoạt WebGL High-DPI Framebuffer (`HD_Texture_Scale.js`)**:
   Instead of forcing the image into a tiny canvas, we expand the GPU's internal render buffer to 2x:
   ```javascript
   Graphics._createRenderer = function() {
       var options = {
           view: this._canvas,
           resolution: 2.0,   // Internal WebGL buffer = 1632 x 1248!
           antialias: true
       };
       this._renderer = new PIXI.WebGLRenderer(this._width, this._height, options);
   };
   ```
3. **Auto-scale Pictures & Sprites**:
   Hook `Sprite_Picture.prototype.updateScale` to automatically multiply scale by `0.5`:
   ```javascript
   if (this.bitmap.width > 1000) {
       this.scale.x *= 0.5;
       this.scale.y *= 0.5;
   }
   ```
4. **Force GPU Bilinear Filtering**:
   Set `this.__baseTexture.scaleMode = PIXI.SCALE_MODES.LINEAR` so PixiJS hardware-blends pixels smoothly on the GPU.

### Final Verification Result:
In session `67fa5fe0`, when switching from SSAA to Native 2x + `HD_Picture_Scale.js`:
The character's face, eyelashes, and skin immediately transformed into **crystal-clear anime art (2K quality)** with **zero pixelation, zero rỗ, and zero layout displacement**!
