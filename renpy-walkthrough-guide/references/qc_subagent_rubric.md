# TIÊU CHUẨN KIỂM ĐỊNH CỦA SUBAGENT QUALITY CHECK (WALKTHROUGH QC RUBRIC)

Subagent đảm nhận vai trò **Quality Check (QC Verifier)** chịu trách nhiệm cao nhất về tính chính xác, thẩm mỹ và tính khả thi của bản hướng dẫn trước khi người dùng nhìn thấy.

---

## 1. Nhiệm Vụ Bắt Buộc Của QC Subagent
1. **Kiểm tra trực quan toàn bộ hình ảnh (Visual Inspection)**:
   - Mở từng file ảnh chụp in-game trong thư mục `images/`.
   - Kiểm tra xem chữ trong hộp thoại có bị:
     - Đè lên nhau (Text overlapping)?
     - Tràn ra ngoài khung hộp thoại (Overflow clipping)?
     - Đè lên các nút bấm lựa chọn hoặc bảng chỉ số HUD?
   - Kiểm tra nhân vật: Có bị cắt mất đầu/thân, đứng sai tọa độ, hoặc che khuất điểm tương tác quan trọng không?
2. **Kiểm tra tính hợp lý & logic game (Logic & Sanity Check)**:
   - Các bước có thực hiện được tuần tự trong game thật không?
   - Có bước nào đòi hỏi người chơi dùng một món đồ mà các bước trước chưa hướng dẫn nhặt/mua không?
   - Cảnh báo Game Over: Đã chỉ ra rõ lựa chọn nào sẽ dẫn đến chết/thua và lựa chọn nào an toàn chưa?
3. **Chạy công cụ kiểm tra tự động**:
   ```bash
   python renpy-walkthrough-guide/scripts/audit_walkthrough_qc.py "<PATH_TO_WALKTHROUGH.md>"
   ```
   - Điểm số **QC Health Score phải đạt từ 95/100 trở lên**.
   - 0 link ảnh bị gãy (Broken link = 0).
   - 0 ký tự giữ chỗ bỏ sót (`[TODO]`, `[Chèn ảnh]`, `[Chưa rõ]`).

---

## 2. Tiêu Chí Đánh Giá (Rubric)

| Tiêu chí | Trọng số | Yêu cầu đạt chuẩn |
| :--- | :--- | :--- |
| **Tính chân thực đồ họa** | 30% | Ảnh chụp giống 100% màn hình game đang chạy (nền, nhân vật, textbox, font tiếng Việt rõ nét). |
| **Không lỗi thị giác** | 25% | Tuyệt đối không đè chữ, không lệch khung thoại, không răng cưa vỡ nét. |
| **Chính xác theo mã nguồn** | 25% | Tọa độ nhấp chuột, tên biến số, điều kiện rẽ nhánh và cạm bẫy khớp 100% với code game. |
| **Trải nghiệm người đọc** | 20% | Có bảng mục lục tổng quan, có cả định dạng Markdown và HTML tương tác dark-mode sang trọng. |
