---
name: rpgmaker-texture-upscaler
description: AI-powered texture and graphic upscaler for RPG Maker MV/MZ games (.rpgmvp encrypted & .png) using DirectML GPU acceleration, Native 2x Super-Resolution, in-memory crypto, and the High-DPI PixiJS WebGL canvas plugin (HD_Texture_Scale.js).
---

# RPG Maker MV/MZ AI Texture Upscaler Skill

Quy trình nâng cấp đồ họa, làm nét CG sự kiện, tranh minh họa H-scene, biểu cảm Face và Spritesheet tự động dành riêng cho game chạy engine **RPG Maker MV & MZ** (hỗ trợ cả tệp mã hóa `.rpgmvp` lẫn ảnh gốc `.png`). Kế thừa toàn bộ bài học thực chiến, giải mã in-memory, chống vỡ hạt 16-bit và hook WebGL High-DPI từ phiên thử nghiệm [67fa5fe0-f3de-4b0a-a15c-5823adf81816](conversation://67fa5fe0-f3de-4b0a-a15c-5823adf81816).

---

## 1. Bản Đồ Tư Duy & Các Bài Học Đắt Giá Từ Thực Tế

### 🌟 Bài học 1: Bẫy Phóng Đại Răng Cưa Do Thu Nhỏ SSAA Trên Canvas Nhỏ (816x624)
> [!CAUTION]
> **Đây là sai lầm nguy hiểm nhất từng gặp ở phiên `67fa5fe0`:**
> - Trong RPG Maker MV, khung hình canvas chỉ có độ phân giải **$816 \times 624$ (chỉ 0.5 Megapixel)**.
> - Khi dùng AI làm nét rồi ép thu nhỏ (SSAA Lanczos) về lại $816 \times 624$, mật độ pixel quá ít không đủ chỗ để vẽ dải màu chuyển tiếp (Anti-aliasing gradient).
> - **Hậu quả**: Nét vẽ vector siêu mảnh bị ép thành các bậc thang vuông 1-pixel thô kệch, biến tranh vẽ anime thành game pixel retro 16-bit (*"bị rỗ hạt, mất hình thù"*).
> - **GIẢI PHÁP CHUẨN XÁC**: **TUYỆT ĐỐI KHÔNG ÉP THU NHỎ BẰNG SSAA**. Bắt buộc giữ nguyên độ phân giải thực **Native 2x** ($1632 \times 1248$) kết hợp với plugin High-DPI của engine.

### 🌟 Bài học 2: Giải Pháp WebGL High-DPI Canvas & Smart Texture Scaler (`HD_Texture_Scale.js`)
- Khi giữ ảnh ở độ phân giải Native 2x ($1632 \times 1248$), `Sprite_Picture` mặc định sẽ hiển thị ảnh phóng to 200% và tràn ra ngoài màn hình.
- **Giải pháp triệt để**: Cài đặt plugin `HD_Texture_Scale.js`:
  1. **WebGL Resolution 2.0**: Mở rộng bộ đệm render nội bộ của GPU lên $1632 \times 1248$ (`resolution: 2.0`, `antialias: true`) giúp game khi bật toàn màn hình (Fullscreen) hiển thị siêu nét.
  2. **Auto Picture Scale**: Tự động co tỷ lệ `scale.set(0.5, 0.5)` trên các ảnh tranh CG/Pictures 2x ($> 1000px$), vừa khít tọa độ logic của game mà không làm hỏng bất kỳ event nào.
  3. **Auto Face Scale**: Hook hàm `Window_Base.prototype.drawFace`, tự động đọc Face 2x ($288 \times 288$ mỗi ô) và vẽ vừa vặn vào khung thoại $144 \times 144$.
  4. **Force GPU Bilinear Filtering**: Ép `scaleMode = PIXI.SCALE_MODES.LINEAR` để PixiJS luôn khử răng cưa mượt mà bằng phần cứng.

### 🌟 Bài học 3: Giải Mã & Tái Mã Hóa In-Memory (.rpgmvp <-> .png)
- Hầu hết game RPG Maker MV/MZ thương mại đều mã hóa ảnh thành định dạng `.rpgmvp`.
- **Cơ chế**: 16 bytes đầu là chữ ký `RPGMV`, 16 bytes tiếp theo bị che mặt nạ XOR bởi `encryptionKey` trong `System.json`, phần còn lại là mã PNG nén tiêu chuẩn.
- **Xử lý trong RAM**: Script tự động trích xuất key từ `www/data/System.json`, giải mã trong bộ nhớ, đưa vào GPU DirectML upscale và tái mã hóa lại thành `.rpgmvp` chuẩn xác 100%. Không làm rò rỉ file PNG rời ra ngoài, giữ nguyên cấu trúc phân phối của game.

### 🌟 Bài học 4: Phân Loại Tài Nguyên & Độ An Toàn (Asset Categories)
- **`pictures/` (Khuyên dùng ưu tiên số 1)**: Chứa toàn bộ CG sự kiện, H-scenes, tranh chân dung nhân vật. Upscale 2x đạt độ nét cao nhất, an toàn 100% không ảnh hưởng gameplay.
- **`faces/`**: Biểu cảm hội thoại (8 mặt/tấm). Upscale 2x nét gấp đôi khi nhân vật nói chuyện.
- **`characters/`**: Spritesheet bước đi. An toàn với hook `Sprite_Character`.
- **`tilesets/`**: Map tileset ($48 \times 48$). Cần chú ý vì grid gạch có thể bị lem viền nếu tilemap engine không căn chỉnh subpixel.

### 🌟 Bài học 5: Giao Thức Bắt Buộc Sao Lưu Bản Gốc 100% & Khôi Phục 1-Click (`restore_backup.py`)
> [!CAUTION]
> **ĐIỀU KIỆN TIÊN QUYẾT BẤT KHẢ XÂM PHẠM (BACKUP-FIRST MANDATE)**:
> Tuyệt đối không bao giờ được phép ghi đè, sửa đổi, thay thế hoặc upscale bất kỳ tệp đồ họa nào khi chưa tạo bản sao lưu nguyên bản (Pristine Backup) 100%.
> - Mọi tệp gốc trước khi can thiệp đều được tự động sao lưu nguyên vẹn vào `backup_textures/original_textures/`.
> - Kịch bản `batch_upscale.py` tích hợp sẵn lớp bảo vệ Backup Guard: trước khi thay thế bất kỳ texture nào, nếu phát hiện bản gốc chưa được backup, script sẽ tự động tạo backup ngay lập tức.
> - Nếu phát sinh bất kỳ lỗi hiển thị, rỗ hạt hoặc người dùng muốn quay về bản gốc, chỉ cần chạy 1 lệnh `restore_backup.py` để khôi phục byte-for-byte trong 5 giây.

---

## 2. Giao Thức Phân Chia Subagent Bắt Buộc (Mandatory Subagents)

Khi triển khai nâng cấp đồ họa một tựa game RPG Maker, BẮT BUỘC sử dụng 3 Subagent chuyên trách:

1. **`rpg-texture-auditor`**: Quét sâu `www/img/`, phát hiện mã hóa, trích xuất key từ `System.json`, sao lưu bản gốc và xuất `manifest.json`.
2. **`rpg-upscale-worker`**: Vận hành engine DirectML GPU (Real-ESRGAN Anime 6B), giải mã/tái mã hóa `.rpgmvp` in-memory, upscale Native 2x và cập nhật `status.json`.
3. **`rpg-qc-verifier`**: Cài đặt plugin `HD_Texture_Scale.js`, kiểm định 100% header PNG, kiểm tra kích thước Native 2x, loại trừ rủi ro SSAA và tạo báo cáo Before/After trực quan.

---

## 3. Quy Trình 4 Bước Triển Khai Chuẩn (Standard Workflow)

```
┌────────────────────────────────────────────────────────┐
│ BƯỚC 1: Quét Toàn Diện & Lập Manifest                  │
│ python scripts/scan_and_manifest.py --game-dir <path>  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ BƯỚC 2: Upscale GPU Native 2x (DirectML Real-ESRGAN)   │
│ python scripts/batch_upscale.py --category pictures    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ BƯỚC 3: Cài Đặt Plugin Co Giãn PixiJS High-DPI        │
│ python scripts/install_hd_plugin.py --game-dir <path>  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ BƯỚC 4: Kiểm Định Chất Lượng Tự Động & Xuất Catalog    │
│ python scripts/audit_upscale_qc.py                     │
│ python scripts/generate_comparison_catalog.py          │
└────────────────────────────────────────────────────────┘
```

---

## 4. Cẩm Nang Lệnh CLI & Cách Sử Dụng

### Bước 1: Quét và Lập Manifest Toàn Bộ Game
```bash
python scripts/scan_and_manifest.py --game-dir "D:/Games/MyRPGMakerGame"
```
*Tác dụng*: Tự động đọc key từ `System.json`, phân loại tài nguyên (`pictures`, `faces`, `characters`, v.v.), sao lưu toàn bộ ảnh gốc vào `backup_textures/original_textures/` và lập file `backup_textures/manifest.json`.

### Bước 2: Chạy Batch Upscale Native 2x Bằng GPU
```bash
# Khuyên dùng: Upscale toàn bộ CG sự kiện & tranh ảnh (pictures)
python scripts/batch_upscale.py --game-dir "D:/Games/MyRPGMakerGame" --category pictures --mode native2x

# Thử nghiệm 2 ảnh đầu tiên để kiểm tra trước
python scripts/batch_upscale.py --game-dir "D:/Games/MyRPGMakerGame" --category pictures --limit 2

# Upscale toàn bộ biểu cảm Face
python scripts/batch_upscale.py --game-dir "D:/Games/MyRPGMakerGame" --category faces --mode native2x

# Upscale tất cả các mục
python scripts/batch_upscale.py --game-dir "D:/Games/MyRPGMakerGame" --category all --mode native2x
```

### Bước 3: Cài Đặt Plugin Co Giãn `HD_Texture_Scale.js`
```bash
python scripts/install_hd_plugin.py --game-dir "D:/Games/MyRPGMakerGame"
```
*Tác dụng*: Tự động sao chép `HD_Texture_Scale.js` vào thư mục `plugins/` của game, sao lưu `plugins.js.bak` và kích hoạt plugin trong `plugins.js`.

### Bước 4: Kiểm Định Chất Lượng Tự Động (QC Audit)
```bash
python scripts/audit_upscale_qc.py --game-dir "D:/Games/MyRPGMakerGame" --category pictures
```
*Tác dụng*: Kiểm tra 100% độ phủ, xác nhận tính toàn vẹn của mã hóa `.rpgmvp` (kiểm tra magic bytes PNG sau giải mã), xác nhận kích thước chuẩn 2x và cảnh báo nếu có ảnh nào bị hạ cấp SSAA.

### Bước 5: Tạo Danh Mục Before / After So Sánh Trực Quan
```bash
python scripts/generate_comparison_catalog.py --game-dir "D:/Games/MyRPGMakerGame" --samples 10
```
*Tác dụng*: Tự động giải mã ảnh gốc và ảnh mới, ghép ảnh Before/After cạnh nhau và xuất file Markdown `backup_textures/catalog/upscale_catalog.md`.

### Khôi Phục Bản Gốc Khẩn Cấp (Emergency Rollback)
```bash
python scripts/restore_backup.py --game-dir "D:/Games/MyRPGMakerGame"
```
*Tác dụng*: Khôi phục 100% tệp gốc byte-for-byte và trả lại trạng thái ban đầu của `plugins.js`.

---

## 5. Tiêu Chuẩn Nghiệm Thu Kỹ Thuật (Quality Checklist)
- [ ] **Native 2x Strict Parity**: Toàn bộ CG sự kiện được nâng cấp lên kích thước Native 2x ($1632 \times 1248$ hoặc tương đương), tuyệt đối không dùng SSAA thu nhỏ.
- [ ] **Mã Hóa Tương Thích Hoàn Hảo**: Tệp `.rpgmvp` sau khi upscale có thể mở mượt mà trong engine game, kiểm tra magic header khớp với PNG tiêu chuẩn.
- [ ] **Kích Hoạt High-DPI Canvas**: Plugin `HD_Texture_Scale.js` đã được bật (`true`) trong `plugins.js`, đảm bảo WebGL render mượt mà khi chạy Fullscreen.
- [ ] **Bảo Toàn Kênh Alpha (Zero Halo)**: Độ trong suốt quanh rìa sprite nhân vật mềm mại, không có viền đen hoặc vạch răng cưa.
- [ ] **Bản sao lưu an toàn**: Thư mục `backup_textures/original_textures/` và `plugins.js.bak` nguyên vẹn.
