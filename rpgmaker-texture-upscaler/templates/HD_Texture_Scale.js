//=============================================================================
// HD_Texture_Scale.js
//=============================================================================
/*:
 * @plugindesc [v2.5] High-DPI WebGL Canvas & Smart 2x HD Texture Scaler for RPG Maker MV/MZ
 * @author Antigravity AI Engine
 *
 * @help
 * Plugin này nâng cấp toàn diện hệ thống hiển thị của RPG Maker MV/MZ:
 * 1. Kích hoạt WebGL High-DPI Canvas (resolution: 2.0 = 1632x1248 buffer)
 *    giúp đồ họa khi phóng to toàn màn hình không bị rỗ hạt hay vỡ nét.
 * 2. Tự động scale 0.5x cho CG/Pictures 2x (độ phân giải > 1000px) để vừa khít màn hình.
 * 3. Tự động scale cho Face 2x (288x288 per face) trong khung hội thoại Window_Base.
 * 4. Tự động scale 0.5x cho Character Sprites 2x trên bản đồ di chuyển.
 * 5. Ép bộ lọc GPU Bilinear Texture Filtering cho hình ảnh mịn màng, sắc nét tuyệt đối.
 */

(function() {
    'use strict';

    var RESOLUTION_SCALE = 2.0;

    // 1. Kích hoạt High-DPI WebGL Canvas Renderer
    var _Graphics_createRenderer = Graphics._createRenderer;
    Graphics._createRenderer = function() {
        if (typeof PIXI !== 'undefined') {
            PIXI.dontSayHello = true;
        }
        var width = this._width;
        var height = this._height;
        var options = {
            view: this._canvas,
            resolution: RESOLUTION_SCALE,
            antialias: true
        };
        try {
            switch (this._rendererType) {
            case 'canvas':
                this._renderer = new PIXI.CanvasRenderer(width, height, options);
                break;
            case 'webgl':
                this._renderer = new PIXI.WebGLRenderer(width, height, options);
                break;
            default:
                this._renderer = PIXI.autoDetectRenderer(width, height, options);
                break;
            }

            if (this._renderer && this._renderer.textureManager) {
                this._renderer.textureManager.maxTextures = 16;
            }
            if (this._renderer) {
                this._renderer.autoResize = false;
            }
        } catch (e) {
            this._renderer = null;
        }
    };

    // 2. Cập nhật kích thước canvas vật lý theo tỷ lệ resolution
    var _Graphics_updateCanvas = Graphics._updateCanvas;
    Graphics._updateCanvas = function() {
        var res = (this._renderer && this._renderer.resolution) ? this._renderer.resolution : RESOLUTION_SCALE;
        this._canvas.width = Math.round(this._width * res);
        this._canvas.height = Math.round(this._height * res);
        this._canvas.style.zIndex = 1;
        this._canvas.style.imageRendering = 'auto'; // Bilinear CSS scaling
        this._centerElement(this._canvas);
    };

    // 3. Căn giữa canvas đúng tỷ lệ tọa độ logic thay vì kích thước buffer vật lý
    Graphics._centerElement = function(element) {
        var width, height;
        if (element === this._canvas) {
            width = this._width * this._realScale;
            height = this._height * this._realScale;
        } else {
            width = element.width * this._realScale;
            height = element.height * this._realScale;
        }
        element.style.position = 'absolute';
        element.style.margin = 'auto';
        element.style.top = 0;
        element.style.left = 0;
        element.style.right = 0;
        element.style.bottom = 0;
        element.style.width = width + 'px';
        element.style.height = height + 'px';
    };

    // 4. Hook Sprite_Picture: Tự động co 0.5x cho tranh 2x (> 1000px)
    if (typeof Sprite_Picture !== 'undefined') {
        var _Sprite_Picture_updateScale = Sprite_Picture.prototype.updateScale;
        Sprite_Picture.prototype.updateScale = function() {
            _Sprite_Picture_updateScale.call(this);
            if (this.bitmap && this.bitmap.isReady()) {
                if (this.bitmap.width > 1000) {
                    this.scale.x *= 0.5;
                    this.scale.y *= 0.5;
                }
            }
        };
    }

    // 5. Hook Window_Base.prototype.drawFace: Hỗ trợ Face 2x (288x288 per cell)
    if (typeof Window_Base !== 'undefined') {
        var _Window_Base_drawFace = Window_Base.prototype.drawFace;
        Window_Base.prototype.drawFace = function(faceName, faceIndex, x, y, width, height) {
            width = width || Window_Base._faceWidth;
            height = height || Window_Base._faceHeight;
            var bitmap = ImageManager.loadFace(faceName);
            if (bitmap && bitmap.isReady() && bitmap.width > 600) {
                // Face sheet 2x detected (e.g. 1152x576 instead of 576x288)
                var pw = Window_Base._faceWidth * 2;
                var ph = Window_Base._faceHeight * 2;
                var sw = Math.min(width * 2, pw);
                var sh = Math.min(height * 2, ph);
                var dx = Math.floor(x + Math.max(width - width, 0) / 2);
                var dy = Math.floor(y + Math.max(height - height, 0) / 2);
                var sx = (faceIndex % 4) * pw + (pw - sw) / 2;
                var sy = Math.floor(faceIndex / 4) * ph + (ph - sh) / 2;
                this.contents.blt(bitmap, sx, sy, sw, sh, dx, dy, width, height);
            } else {
                _Window_Base_drawFace.call(this, faceName, faceIndex, x, y, width, height);
            }
        };
    }

    // 6. Hook Sprite_Character: Tự động co 0.5x cho Character Sprite 2x
    if (typeof Sprite_Character !== 'undefined') {
        var _Sprite_Character_updateBitmap = Sprite_Character.prototype.updateBitmap;
        Sprite_Character.prototype.updateBitmap = function() {
            _Sprite_Character_updateBitmap.call(this);
            if (this.bitmap && this.bitmap.isReady()) {
                // In MV, 48px tile * 3 cols = 144px per character min. If 2x, > 250px.
                if (this.bitmap.width > 300 && !this._hdCharacterScaled) {
                    this.scale.set(0.5, 0.5);
                    this._hdCharacterScaled = true;
                }
            }
        };
    }

    // 7. Hook Sprite tổng quát cho phòng trưng bày CG hoặc cảnh H-scene đặc thù
    if (typeof Sprite !== 'undefined') {
        var _Sprite_update = Sprite.prototype.update;
        Sprite.prototype.update = function() {
            _Sprite_update.call(this);
            if (this._isRecollectionCGSprite && this.bitmap && this.bitmap.isReady()) {
                if (this.bitmap.width > 1000 && !this._hdScaled) {
                    this.scale.set(0.5, 0.5);
                    this._hdScaled = true;
                }
            }
        };
    }

    // 8. Đảm bảo BaseTexture của Bitmap luôn dùng Linear filtering
    if (typeof Bitmap !== 'undefined' && Bitmap.prototype._createBaseTexture) {
        var _Bitmap_createBaseTexture = Bitmap.prototype._createBaseTexture;
        Bitmap.prototype._createBaseTexture = function(source) {
            _Bitmap_createBaseTexture.call(this, source);
            if (this.__baseTexture && typeof PIXI !== 'undefined') {
                this.__baseTexture.scaleMode = PIXI.SCALE_MODES.LINEAR;
            }
        };
    }

})();
