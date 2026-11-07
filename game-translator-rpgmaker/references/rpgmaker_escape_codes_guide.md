# RPG Maker Escape & Control Codes Reference Guide

RPG Maker uses escape codes inside strings to dynamically display variables, actor names, colors, icons, and timing pauses.
**Zero-Tolerance Rule**: Control codes must be preserved with 100% fidelity. Never remove, translate, or replace them with hardcoded names unless explicitly instructed.

---

## 1. Dynamic Replacement Codes

| Escape Code | Description | Example & Meaning | Localization Note |
|---|---|---|---|
| `\V[n]` | Value of Variable `n` | `Bạn nhận được \V[10] vàng!` | Giữ nguyên `\V[10]`. |
| `\N[n]` | Name of Actor (Character) `n` | `Chào \N[1], hôm nay thế nào?` | Tra cứu `\N[1]` trong Lorebook để biết giới tính/đại từ xưng hô, nhưng giữ nguyên mã `\N[1]` trong câu dịch! |
| `\P[n]` | Name of Party Member in slot `n` | `Đi theo tôi, \P[1]!` | Tương tự `\N[n]`, giữ nguyên mã. |
| `\G` | Currency Unit | `Giá: 500 \G` | Hiển thị đơn vị tiền tệ (G, Vàng, Yên). |

---

## 2. Text Formatting & Styling Codes

| Escape Code | Description | Example & Meaning | Localization Note |
|---|---|---|---|
| `\C[n]` | Text Color `n` (0–31) | `\C[2]Vật phẩm quý hiếm\C[0]` | Đổi màu chữ theo bảng màu `Window.png`. `\C[0]` hoàn nguyên về màu trắng mặc định. |
| `\I[n]` | Draw Icon `n` | `\I[64] Kiếm Sắt` | Vẽ icon từ `IconSet.png`. Phải đi liền với tên vật phẩm. |
| `\{` | Increase font size by 1 step | `\C[2]\{CẢNH BÁO!\} ` | Chữ to hơn. Thường đi thành cặp `\{ ... \}`. |
| `\}` | Decrease font size by 1 step | `\}Lời thì thầm...\{` | Chữ nhỏ hơn. Thường đi thành cặp `\} ... \{`. |

---

## 3. Timing, Sound & Dialog Flow Codes

| Escape Code | Description | Meaning in Game |
|---|---|---|
| `\.` | Wait 1/4 second (15 frames) | Tạo khoảng nghỉ ngập ngừng trong câu nói. |
| `\|` | Wait 1 second (60 frames) | Tạm dừng kịch tính trước khi nói tiếp. |
| `\!` | Wait for player input | Bắt người chơi bấm phím/click chuột mới hiện phần tiếp theo. |
| `\>` | Instant display ON | Tắt hiệu ứng gõ chữ từng ký tự, hiện ngay lập tức cả đoạn. |
| `\<` | Instant display OFF | Bật lại hiệu ứng gõ chữ từng ký tự. |
| `\^` | Do not wait for input | Tự động chuyển trang thoại mà không cần click chuột. |
| `\$` | Open gold window | Mở cửa sổ tiền tệ ở góc màn hình. |

---

## 4. Plugin Chevron Tags (Yanfly, VisuStella, etc.)

Many RPG Maker games use advanced message plugins that define custom chevron tags:
- `<WordWrap>`: Bật chế độ tự ngắt dòng tự động của plugin.
- `<Speaker: Alice>`: Đặt tên người nói trên đầu hộp thoại.
- `<face: Actor1, 2>`: Đổi ảnh mặt nhân vật giữa chừng.
- `<Target: All>`: Thiết lập mục tiêu kỹ năng.

**BẮT BUỘC**: Tất cả thẻ `<...>` phải được giữ nguyên vị trí và định dạng. Không bao giờ dịch nội dung bên trong cặp dấu `< >`.
