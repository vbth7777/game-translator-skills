# CẨM NANG KHẮC PHỤC LỖI FONT TOFU BOX ([?]) TRONG REN'PY

Lỗi ô vuông có dấu chấm hỏi `[?]` (Tofu box) xuất hiện khi font chữ đang sử dụng thiếu các ký tự Unicode tiếng Việt có dấu (ví dụ: `ồ`, `ừ`, `ặ`, `ẫ`, `ẻ`...).

---

## 1. Nguyên nhân cốt lõi trong Ren'Py
1. **Thiếu Glyph trong file Font gốc**: Đa số game phương Tây hoặc Nhật Bản chỉ nạp các font chứa ký tự Latin cơ bản (ASCII + Latin-1 Supplement), thiếu hoàn toàn 134 glyphs của bảng chữ cái tiếng Việt.
2. **Quy định thứ tự ưu tiên của Ren'Py Engine**:
   - Khi tìm kiếm file tài nguyên (font, image, script), Ren'Py luôn tìm trong thư mục rời `game/` trước khi tìm trong gói nén `game/archive.rpa`.
   - **Tận dụng quy luật này**: Không cần phải sửa file `archive.rpa`, chỉ cần đặt đè font cùng tên vào thư mục `game/fonts/`!

---

## 2. Quy trình 3 bước xử lý triệt để

### Bước 1: Quét và phát hiện font thiếu ký tự
Chạy công cụ kiểm tra font:
```bash
python game-translator-renpy/scripts/audit_fonts.py "<GAME_PATH>/scratch/fonts"
```
Kết quả sẽ liệt kê chính xác các font không đạt 100% (ví dụ: `HPSimplified.ttf` thiếu 92 glyphs).

### Bước 2: Chuẩn bị Font Unicode thay thế
Sử dụng các font chuẩn hỗ trợ 100% tiếng Việt:
- `OpenSans_SemiCondensed-Regular.ttf` (Nét hiện đại, thon gọn)
- `DejaVuSans.ttf` (Font mặc định của Ren'Py, hỗ trợ Unicode toàn cầu)
- `segoeui.ttf` / `seguibl.ttf` (Segoe UI của Windows, sắc nét cho UI/Dialogue)

### Bước 3: Đặt đè (Override)
1. Tạo thư mục `game/fonts/` (nếu chưa có).
2. Copy font chuẩn Unicode tiếng Việt đổi tên thành đúng tên file font bị lỗi và đặt vào `game/fonts/`.
3. Khai báo phong cách chữ mặc định trong `game/tl/vietnamese/common.rpy`:
```renpy
translate vietnamese style default:
    font "fonts/OpenSans_SemiCondensed-Regular.ttf"

translate vietnamese style normal_menu_button_text:
    font "DejaVuSans.ttf"
```
Khi game khởi động, Ren'Py sẽ tự động nạp font ngoài thư mục `game/fonts/`, giải quyết 100% lỗi tofu box trên mọi màn hình và nút bấm.

