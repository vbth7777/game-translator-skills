# RPG Maker MV/MZ Graphic Asset Architecture & Grid Dimensions

## 1. Directory Structure Overview

All visual assets reside inside `www/img/` (RPG Maker MV) or `img/` (RPG Maker MZ):

```
www/img/
├── pictures/       # Event illustrations, CGs, H-scenes, bust portraits, cut-ins
├── faces/          # Character dialogue expressions (8 faces per sheet)
├── characters/     # Walking map spritesheets ($ single, normal 8-character)
├── tilesets/       # Map tiles (A1-A5 autotiles, B, C, D, E normal tiles)
├── animations/     # Spell, weapon, and battle visual effect strips
├── battlebacks1/   # Combat floor / terrain backdrops
├── battlebacks2/   # Combat sky / horizon backdrops
├── titles1/        # Main title screen background artwork
├── titles2/        # Main title screen frames / overlays
├── parallaxes/     # Scrolling background layers (fog, clouds, water)
└── system/         # Window.png, IconSet.png, Balloon.png, GameOver.png
```

---

## 2. Dimensional Standards & Grid Formulas

### A. Pictures (`www/img/pictures/`)
- **Default Resolution**: Typically matches game screen resolution ($816 \times 624$ in MV, $1280 \times 720$ in MZ), or custom resolutions for event bust portraits.
- **Engine Logic**: Rendered via `Sprite_Picture`.
- **2x Scaling Strategy**: Upscale to Native 2x ($1632 \times 1248$). In-game `HD_Texture_Scale.js` automatically applies `scale.set(0.5, 0.5)` if `bitmap.width > 1000`.

### B. Faces (`www/img/faces/`)
- **Grid Layout**: 4 columns $\times$ 2 rows = 8 expressions per sheet.
- **Tile Dimensions**:
  - MV / MZ: $144 \times 144$ pixels per face $\rightarrow$ Sheet size: $576 \times 288$.
  - Native 2x Upscale: $288 \times 288$ pixels per face $\rightarrow$ Sheet size: $1152 \times 576$.
- **Engine Logic**: `Window_Base.prototype.drawFace(faceName, faceIndex, x, y, width, height)`.
- **Hook Requirement**: `HD_Texture_Scale.js` intercepts `drawFace`, doubling source sampling coordinates $(pw = 288, ph = 288)$ while drawing into destination bounding box ($144 \times 144$) via GPU `blt`.

### C. Characters (`www/img/characters/`)
- **Grid Layout**:
  - Single character (filename starting with `$`, e.g. `$Hero.png`): 3 columns $\times$ 4 directions = 12 frames.
  - Multi-character sheet (8 characters): 12 columns $\times$ 8 rows = 96 frames.
- **Tile Dimensions**:
  - MV / MZ: $48 \times 48$ per tile.
  - VX Ace: $32 \times 32$ per tile.
  - XP: $24 \times 24$ per tile.
- **Engine Logic**: `Sprite_Character.prototype.updateBitmap` determines frame width:
  $$\text{frameWidth} = \frac{\text{bitmap.width}}{3 \text{ or } 12}, \quad \text{frameHeight} = \frac{\text{bitmap.height}}{4 \text{ or } 8}$$
- **Hook Requirement**: If character sheet is 2x, RPG Maker naturally slices 2x frames, but `scale.set(0.5, 0.5)` must be applied so the character's footprint on the map remains 1 tile ($48 \times 48$ logical).

### D. Animations (`www/img/animations/`)
- **Grid Layout**: Fixed 5 columns $\times$ arbitrary rows.
- **Cell Dimensions**: Fixed $192 \times 192$ per animation cell in MV.
- **2x Dimensions**: $384 \times 384$ per cell.

### E. Tilesets (`www/img/tilesets/`)
- **Tile Dimensions**: $48 \times 48$ in MV/MZ, $32 \times 32$ in VX Ace.
- **Grid Integrity Warning**: Pixi-tilemap operates on integer pixel buffers. Upscaling tilesets requires WebGL High-DPI canvas to prevent tile bleeding / seam artifacts across grid borders.
