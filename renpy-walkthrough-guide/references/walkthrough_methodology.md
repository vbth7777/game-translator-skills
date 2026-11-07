# PHƯƠNG PHÁP & QUY CHUẨN XÂY DỰNG WALKTHROUGH CHO GAME REN'PY

Tài liệu này đúc kết phương pháp luận từ phiên làm việc thực tế (`62e271c6-f25b-4c18-b886-b2451f3f445a`) về cách xây dựng một bộ Cẩm nang Hướng dẫn (Walkthrough & Guideline) đạt chuẩn chất lượng cao nhất theo ý người dùng.

---

## 1. Triết Lý Cốt Lõi: Trải Nghiệm Nhập Vai Như Người Chơi Thật (Authentic Playthrough)
- **Không làm bản tóm tắt lý thuyết khô khan**: Người dùng không muốn đọc những danh sách gạch đầu dòng mơ hồ kiểu *"Đi đến bãi biển, nói chuyện với Nami rồi vào hang"*.
- **Mô phỏng chân thực như có người đã chơi trước và chụp ảnh từng bước**:
  - Hướng dẫn phải có cấu trúc theo từng bước tuần tự (Bước 1 -> Bước 2 -> Bước 3...).
  - Mỗi bước bắt buộc kèm theo **Ảnh chụp màn hình in-game thực tế** thể hiện đúng bối cảnh, nhân vật, hộp thoại và vị trí tương tác.
  - Thể hiện rõ: Tọa độ nhấp chuột, gợi ý lựa chọn tối ưu, và các cạm bẫy Game Over chết người.

---

## 2. Quy Trình 5 Bước Tiêu Chuẩn

```
[Mã nguồn Ren'Py .rpy/.rpyc]
          │
          ├──> Bước 1: Khảo sát Logic & Phân nhánh (`analyze_renpy_routes.py`)
          │            (Không bao giờ đoán mò; trích xuất chính xác điều kiện cờ, biến số, vật phẩm)
          │
          ├──> Bước 2: Thiết kế Lộ trình Bước (Step Blueprint)
          │            (Phân chia thành các Phần I, II, III theo mạch sự kiện hợp lý)
          │
          ├──> Bước 3: Dựng Ảnh Chụp Mockup In-Game (`generate_walkthrough_screens.py`)
          │            (Nạp asset game: Nền, Nhân vật, Hộp thoại, Tự động wrap text)
          │
          ├──> Bước 4: Kiểm Định Chất Lượng Bắt Buộc Qua Subagent QC (`audit_walkthrough_qc.py`)
          │            (Mắt xích sống còn: Soi từng ảnh, phát hiện lỗi đè text, sai tọa độ, phi lý)
          │
          └──> Bước 5: Xuất Bản Hai Định Dạng (Markdown .md & Interactive HTML .html)
```

---

## 3. Các Cạm Bẫy Cần Tránh (Rút ra từ Sự Cố Thực Tế)

1. **Bỏ sót điều kiện tiên quyết (Prerequisite Items)**:
   - *Ví dụ*: Đến hang đá Nami đòi đập đá nhưng người chơi chưa mua Cuốc Chim ($70) ở Chợ Bazzar thì game sẽ kẹt hoặc Game Over.
   - *Quy tắc*: Luôn rà soát cờ điều kiện (`if inv.has(...)`) trong mã nguồn trước khi viết bước tiếp theo.
2. **Lỗi đè chữ và tràn hộp thoại trong ảnh mockup**:
   - Nếu câu thoại quá dài, chữ sẽ tràn ra ngoài khung `textbox.png` hoặc đè lên nút lựa chọn `choice_idle`.
   - *Quy tắc*: Bắt buộc dùng hàm tự động ngắt dòng (`wrap_text`) với giới hạn tối đa 3–4 dòng, chiều cao cách nhau 36–38px.
3. **Đặt sai vị trí nhân vật (Sprite Misplacement)**:
   - Nhân vật đứng che mất biển chỉ đường hoặc hộp thoại.
   - *Quy tắc*: Đặt sprite nhân vật tại tọa độ chuẩn từ lệnh `show` trong mã nguồn game (ví dụ: `(x=529, y=386)` hoặc căn chỉnh xalign phù hợp).
4. **Không tự kiểm tra lại hình ảnh trước khi bàn giao**:
   - Đây là nguyên nhân khiến người dùng phàn nàn nhiều nhất. AI tạo ảnh bằng code nhưng không tự đọc lại ảnh để xem có bị lỗi đè chữ, sai phông nền hay không.
   - *Quy tắc*: Bắt buộc giao cho Subagent Quality Check soi từng bức ảnh trước khi xuất báo cáo.
