# QUY CHUẨN DỊCH THUẬT REN'PY (REN'PY TRANSLATION RULES)

## 1. Cấu trúc thư mục chuẩn
Mọi file bản dịch phải nằm dưới:
`game/tl/vietnamese/<script_name>.rpy`

---

## 2. Cú pháp dịch hội thoại (Dialogue Blocks)
Mỗi dòng thoại gốc được định danh bằng một chuỗi mã băm hoặc nhãn (label):

```renpy
# game/script.rpy:45
translate vietnamese start_a1b2c3d4:

    # e "Hello, world!"
    e "Xin chào thế giới!"
```

### Quy tắc bảo toàn thẻ nội suy:
- Biến nội suy: `[player_name]`, `[score]` -> **Giữ nguyên 100% trong ngoặc vuông**.
- Thẻ định dạng: `{b}`, `{/b}`, `{color=#ff0000}`, `{/color}`, `{i}`, `{w=1.0}`, `{p}` -> **Giữ nguyên đúng vị trí**.

Ví dụ chuẩn:
```renpy
# Gốc:
p "Welcome back, {b}[player_name]{/b}! You have {color=#ffdd00}[coins] gold{/color}."

# Dịch chuẩn:
p "Mừng trở lại, {b}[player_name]{/b}! Cậu hiện có {color=#ffdd00}[coins] vàng{/color}."
```

---

## 3. Cú pháp dịch chuỗi hệ thống & UI (`strings:`)
Nằm trong `game/tl/vietnamese/common.rpy`:

```renpy
translate vietnamese strings:

    old "Start Game"
    new "Bắt Đầu"

    old "Preferences"
    new "Cài Đặt"

    old "Return"
    new "Quay Lại"
```

> **LƯU Ý QUAN TRỌNG VỀ INTERPOLATION TRONG `strings:`**:
> Nếu game có cả chuỗi raw `Give her $[MONEY_GIFT_1]` và chuỗi đã tính toán `Give her $50`, hãy khai báo cả hai biến thể trong `common.rpy` để đảm bảo khớp lệnh ở mọi giai đoạn tính toán của engine.

