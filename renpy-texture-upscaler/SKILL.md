---
name: renpy-texture-upscaler
description: AI-powered texture and visual asset upscaling pipeline for Ren'Py games (Live2D 2K/4K texture atlases, static CGs, character busts, wallpapers, UI) using DirectML GPU acceleration, 4-channel alpha preservation, Lanczos SSAA resampling for layout safety, and streaming RPA repacking.
---

# Ren'Py Game Texture & Live2D AI Upscaler Skill

Quy trình nâng cấp đồ họa, làm nét texture và Live2D tự động chuẩn chuyên nghiệp dành riêng cho game chạy engine Ren'Py. Kế thừa toàn bộ bài học thực chiến, giải thuật khử nhiễu AI, chống tràn khung hình 2x và bảo toàn độ trong suốt kênh Alpha từ thực nghiệm trên card rời NVIDIA RTX.

---

## 1. Bản Đồ Tư Duy & Các Bài Học Đắt Giá Từ Thực Tế

### 🌟 Bài học 1: Gốc Rễ Khiến Live2D & Texture Ren'Py Bị Mờ Rỗ
- **Hiện tượng**: Khi chơi game trên màn hình Full HD (1080p), 2K (1440p) hoặc 4K, nhân vật cử động Live2D hoặc các cảnh chiến đấu bị mờ nét, răng cưa viền áo, rỗ hạt.
- **Nguyên nhân kỹ thuật**: Tác giả game xuất Texture Atlas ở kích thước nhỏ (**1024x1024**, **1024x2048**, hoặc thậm chí **512x1024**). Từng bộ phận (mặt, mắt, váy, cơ thể) bị nhồi vào atlas chỉ chiếm 200–300 pixel. Khi nhân vật hiển thị chiếm 80–90% màn hình, OpenGL kéo dãn texture gấp 3x–4x gây nhòe nặng.

### 🌟 Bài học 2: Bẫy Phóng To 2x (2x Zoom Overflow Trap) & Chiến Lược Kép (Dual-Path Strategy)
> [!IMPORTANT]
> **Đây là sai lầm phổ biến nhất khi upscale game Ren'Py:**
> - **Nhân vật Live2D (`.moc3`)**: Sử dụng **Tọa độ UV chuẩn hóa $[0.0, 1.0]$** trên lưới đa giác (polygon mesh). Kích thước hiển thị trên màn hình được cố định bởi khung xương `.moc3`, **không phụ thuộc vào pixel texture**. Do đó, upscale texture atlas lên 2048 hoặc 4096 **hoàn toàn an toàn, nhân vật giữ nguyên vị trí và kích thước, nét căng gấp 4 lần**.
> - **Ảnh tĩnh 2D (Title Logo, Main Menu Wallpaper, Event CG, Character Bust, UI)**: Ren'Py hiển thị ảnh tĩnh theo **tọa độ pixel 1:1**. Nếu game thiết kế ở chuẩn `gui.init(1920, 1080)`, việc upscale thẳng tay ảnh tĩnh lên 4K ($3840 \times 2160$) sẽ khiến hình ảnh bị **phóng đại 200%, tràn ra ngoài viền màn hình (bị cắt cụt nửa hình/logo)**!
> - **GIẢI PHÁP - CHIẾN LƯỢC KÉP**:
>   1. **Path A (Live2D)**: Nâng cấp Native Super-Resolution lên **2048x2048** hoặc **4096x4096**.
>   2. **Path B (Static 2D)**: Dùng kỹ thuật **Super-Sampled Anti-Aliasing (SSAA)**: AI upscale lên 4K để phục hồi nét vẽ vector và khử nhiễu nén, sau đó dùng thuật toán **Lanczos-4** thu nhỏ về đúng kích thước tọa độ gốc ($1920 \times 1080$). Kết quả: Đường nét mượt mà không tì vết, vừa khít 100% layout, triệt tiêu hoàn toàn lỗi phóng to 2x!

### 🌟 Bài học 3: Tối Ưu Hóa GPU Bằng DirectML (Không Cần Cài CUDA Phức Tạp)
- Trên Windows, PyTorch CUDA thường gặp lỗi xung đột phiên bản driver hoặc cài nhầm bản CPU.
- Skill sử dụng **ONNX Runtime với `DmlExecutionProvider` (DirectML)**: Tự động nhận diện và khai thác 100% sức mạnh card đồ họa rời (NVIDIA GeForce RTX, AMD Radeon, Intel Arc) thông qua DirectX 12 với tốc độ xử lý siêu tốc (~6–15 giây cho một texture khổng lồ).

### 🌟 Bài học 4: Bảo Toàn Kênh Alpha 4-Channel (Chống Viền Đen / Lem Độ Trong Suốt)
- Các model AI Super-Resolution (Real-ESRGAN Anime 6B) nguyên bản chỉ nhận 3 kênh màu (RGB). Nếu bỏ qua kênh Alpha, các vùng trong suốt của nhân vật sẽ bị biến thành màu đen hoặc lem viền (border halos/fringing).
- Giải pháp: Áp dụng kiến trúc **Dual-Plane Processing**: Tách riêng kênh Alpha, nhân 3 thành ảnh xám 3 kênh, chạy qua cùng một mạng nơ-ron rồi ghép lại. Toàn bộ viền áo, tóc tơ và chi tiết xuyên thấu giữ độ trong suốt sắc sảo đến từng subpixel.

### 🌟 Bài học 5: Cơ Chế Ghi Đè Không Chạm File Gốc & Repack RPA
- Ren'Py luôn ưu tiên nạp tệp rời trong thư mục `game/` trước tệp đóng gói trong `game/archive.rpa`.
- Trong giai đoạn thử nghiệm, chỉ cần ghi đè file upscaled vào `game/<rel_path>` để kiểm tra ngay lập tức mà không cần giải nén file RPA 1 GB.
- Sau khi kiểm tra hoàn tất, dùng `repack_archive.py` để đóng gói hàng loạt vào RPA và dọn dẹp các tệp rời.

### 🌟 Bài học 6: Quy Tắc Ngưỡng 1080p (Chống Hiện Tượng Rỗ Hạt / Hóa Thành Pixel Game Do SSAA)
- **Bài học xương máu từ RPG Maker MV (`67fa5fe0`)**: Khi áp dụng SSAA thu nhỏ ảnh từ 4K về lại độ phân giải ban đầu, nếu ảnh gốc có kích thước quá nhỏ ($< 1080p$, ví dụ $816 \times 624$ hay $720p$/$480p$), khung hình không có đủ mật độ điểm ảnh để biểu diễn dải chuyển tiếp (anti-aliasing gradient). Thuật toán Lanczos sẽ ép nét vẽ vector thành các bậc thang vuông 1-pixel thô kệch, khiến tranh anime biến thành game retro 16-bit ("bị rỗ hạt / mất hình thù").
- **Ngưỡng an toàn tuyệt đối**:
  1. **Ảnh tĩnh $\ge 1080p$ (như trong Ren'Py PAWGVERSE $1920 \times 1080$, $1920 \times 2511$)**: Áp dụng SSAA Lanczos downsampling là hoàn hảo nhất, triệt tiêu 100% răng cưa và vừa khít layout.
  2. **Ảnh tĩnh $< 1080p$**: **Kích hoạt Guardrail tự động**: BẮT BUỘC giữ nguyên Native 2x (không được thu nhỏ bằng SSAA) để bảo toàn nét vẽ mịn màng, đồng thời dùng template `templates/renpy_hd_override.rpy` hoặc `Transform(zoom=0.5)` để Ren'Py tự scale bằng phần cứng khi hiển thị.

---

## 2. Giao Thức Phân Chia Subagent Bắt Buộc (Mandatory Subagents)

Khi tiến hành nâng cấp đồ họa một tựa game hoàn chỉnh, BẮT BUỘC sử dụng 3 Subagent chuyên trách:

1. **`texture-scanner-auditor`**: Quét sâu thư mục `game/` và tệp `archive.rpa`, phân loại Live2D vs Ảnh tĩnh, đo đạc kích thước và xuất `manifest.json`.
2. **`gpu-upscale-worker`**: Vận hành engine DirectML GPU, xử lý từng đợt (batch), bảo toàn alpha, áp dụng SSAA Lanczos và cập nhật `status.json`.
3. **`upscale-qc-verifier`**: Kiểm định độ phân giải, quét lỗi phóng to 2x trên ảnh tĩnh, kiểm tra viền alpha, chạy Ren'Py Lint và tạo báo cáo so sánh Before/After trực quan.

---

## 3. Quy Trình 4 Bước Triển Khai Chuẩn (Standard Workflow)

```
┌────────────────────────────────────────────────────────┐
│ BƯỚC 1: Quét Toàn Diện & Phân Loại (scan_and_manifest) │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ BƯỚC 2: Upscale GPU Theo Chiến Lược Kép (batch_upscale)│
│  - Live2D  -> Native 2K/4K (2048/4096)                 │
│  - Static  -> SSAA Lanczos (Khử nhiễu & giữ layout)   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ BƯỚC 3: Kiểm Định Chất Lượng & Báo Cáo QC (audit_qc)   │
│  - Quét sạch 100% lỗi phóng to 2x                      │
│  - Xuất bảng Before/After so sánh trực quan            │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ BƯỚC 4: Đóng Gói Archive RPA & Nghiệm Thu (repack_rpa)  │
│  - Sao lưu bản gốc an toàn (.original_backup)          │
│  - Thay thế luồng dữ liệu & Swap nguyên tử             │
└────────────────────────────────────────────────────────┘
```

---

## 4. Cẩm Nang Lệnh CLI & Cách Sử Dụng

### Bước 1: Quét và Lập Manifest Toàn Bộ Game
```bash
python scripts/scan_and_manifest.py --game-dir "D:/Games/MyRenPyGame"
```
*Tác dụng*: Tự động phân loại toàn bộ texture trong thư mục `game/` và trong các tệp `.rpa`, sao lưu bản gốc vào `backup_textures/original_textures/` và lập file `backup_textures/manifest.json`.

### Bước 2: Chạy Batch Upscale Bằng GPU (DirectML)
```bash
# Upscale toàn bộ theo Chiến Lược Kép (Live2D -> 4K, Static -> SSAA Lanczos 1080p)
python scripts/batch_upscale.py --game-dir "D:/Games/MyRenPyGame" --category all

# Chỉ upscale Live2D Textures
python scripts/batch_upscale.py --game-dir "D:/Games/MyRenPyGame" --category live2d

# Chỉ upscale Static Images (CG, Bust, Wallpaper)
python scripts/batch_upscale.py --game-dir "D:/Games/MyRenPyGame" --category static
```

### Bước 3: Kiểm Định Chất Lượng Tự Động (QC Audit)
```bash
python scripts/audit_upscale_qc.py --game-dir "D:/Games/MyRenPyGame"
```
*Tác dụng*: Kiểm tra 100% độ phủ, phát hiện nếu có ảnh tĩnh nào bị lỗi phóng to 2x, kiểm tra viền Alpha và chạy Ren'Py Lint.

### Bước 4: Tạo Danh Mục Before / After So Sánh Trực Quan
```bash
python scripts/generate_comparison_catalog.py
```
*Tác dụng*: Ghép ảnh trước và sau (Before/After) cạnh nhau cho từng nhân vật và xuất file Markdown `upscale_workspace/catalog/upscale_catalog.md` trực quan sinh động.

### Bước 5: Đóng Gói Trở Lại Vào File `archive.rpa`
```bash
python scripts/repack_archive.py --game-dir "D:/Games/MyRenPyGame" --archive archive.rpa --clean-loose
```
*Tác dụng*: Tự động sao lưu `archive.rpa.original_backup`, nhúng các texture đã upscale vào file RPA mới, kiểm tra tính toàn vẹn và dọn dẹp các tệp tạm để giải phóng dung lượng ổ cứng.

---

## 5. Tiêu Chuẩn Nghiệm Thu Kỹ Thuật (Quality Checklist)
- [ ] **100% Độ phủ (Zero Missing Textures)**: Không bỏ sót bất kỳ model Live2D chiến đấu, model phụ, multi-sheet texture (`texture_01.png`), hoặc ảnh nền nào.
- [ ] **Zero 2x Zoom Bug**: Mọi ảnh tĩnh (UI, logo, wallpaper menu, CG) hiển thị vừa vặn hoàn hảo trên viewport, không bị phóng to hay cắt mép.
- [ ] **1080p SSAA Guardrail Enforcement**: Tuyệt đối không ép thu nhỏ bằng SSAA trên ảnh $< 1080p$ để ngăn ngừa triệt để lỗi rỗ nét / biến thành pixel game.
- [ ] **Khử Viền Alpha (Zero Halo)**: Độ trong suốt quanh rìa nhân vật mềm mại, không có viền đen hoặc vạch răng cưa.
- [ ] **Ren'Py Lint Exit Code 0**: Engine Ren'Py nạp dữ liệu hoàn hảo, không có cảnh báo xung đột transform hoặc thiếu file.
- [ ] **Bản sao lưu nguyên vẹn**: Luôn duy trì `archive.rpa.original_backup` và thư mục `backup_textures/original_textures/`.

