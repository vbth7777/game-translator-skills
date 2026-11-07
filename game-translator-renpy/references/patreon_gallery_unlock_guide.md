# CẨM NANG GIẢI MÃ & MỞ KHÓA BỘ SƯU TẬP (PATREON / GALLERY UNLOCK GUIDE)

Trong các Visual Novel và game 18+ dùng Ren'Py, nhà phát triển thường tích hợp cơ chế khóa nội dung (Patreon Gate / Gallery Lock) để giới hạn phân cảnh H-scene, phòng trưng bày CG, hoặc các tính năng đặc biệt cho người ủng hộ trả phí.

---

## 1. Dấu hiệu nhận biết trong mã nguồn Ren'Py
Thường nằm trong:
- `game/patreon_gate.rpy`
- `game/gallery.rpy`
- `game/screens.rpy` (nút Gallery bị disable hoặc gắn điều kiện)
- Biến trạng thái: `persistent.isDm`, `persistent.patreon_unlocked`, `persistent.dlcEntitlements`, `persistent.unlocked_all`

---

## 2. Kỹ thuật 1: Phân tích cơ chế mã băm (SHA256 + Salt)
Nhiều game không lưu mã dạng văn bản rõ mà so khớp mã băm SHA256:

```python
import hashlib
PATREON_SALT = "rbln-7Qk2xVpL9sTfMw3ZdYhC"
EXPECTED_HASH = "679d6a6a3ebf28594672ee9abdc52e1d12674acca71f410ac37311fd187c3e2e"

def check_code(inp):
    return hashlib.sha256((inp.strip() + PATREON_SALT).encode('utf-8')).hexdigest() == EXPECTED_HASH
```

### Phương pháp xử lý:
1. **Dò nhanh các từ khóa phổ biến**: Thử băm danh sách các từ thông dụng của game:
   - Tên game: `REBELLIOUN`, `PAWGVERSE`
   - Tên tác giả / Patreon: `MOCHI`, `PINKMOCHI`, `PATREON`, `BETA`, `TIER3`
   - Chuỗi số: `1234`, `6969`, `7777`
2. **Nếu băm quá phức tạp**: **Không cần tốn thời gian bẻ khóa (brute-force)**! Hãy can thiệp trực tiếp vào mã nguồn `patreon_gate.rpy`!

---

## 3. Kỹ thuật 2: Can thiệp mã nguồn mở khóa vạn năng (Universal Bypass)
Mở tệp `game/patreon_gate.rpy` hoặc tệp kiểm tra mã, bổ sung danh sách mã vạn năng mà không làm hỏng logic gốc:

```python
# Thay vì chỉ kiểm tra băm:
# if hashlib.sha256((code + PATREON_SALT).encode()).hexdigest() == TARGET_HASH:

# Đổi thành:
UNIVERSAL_CODES = {"UNLOCK", "ALL", "BETA", "REBELLIOUN", "1234", "6969"}
if code.strip().upper() in UNIVERSAL_CODES or hashlib.sha256((code + PATREON_SALT).encode()).hexdigest() == TARGET_HASH:
    persistent.patreon_unlocked = True
    persistent.gallery_unlocked = True
    renpy.notify("Đã mở khóa toàn bộ nội dung thành công!")
```

---

## 4. Kỹ thuật 3: Mở khóa bằng File Patch `init python:`
Tạo file patch độc lập (ví dụ `game/unlock_patch.rpy`):

```renpy
init 999 python:
    # Tự động cấp quyền sở hữu cao nhất khi game khởi động
    if hasattr(persistent, "patreon_unlocked"):
        persistent.patreon_unlocked = True
    if hasattr(persistent, "isDm"):
        persistent.isDm = True
    if hasattr(persistent, "all_gallery_unlocked"):
        persistent.all_gallery_unlocked = True
    
    # Kích hoạt bảng điều khiển nhà phát triển
    config.developer = True
```

Cách này không can thiệp vào các file gốc của game, an toàn tuyệt đối khi update bản dịch và giúp người kiểm thử (tester) có thể vào thẳng mọi phân cảnh hồi tưởng/CG để rà soát lỗi dịch thuật.

