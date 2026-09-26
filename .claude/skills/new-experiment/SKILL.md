---
name: new-experiment
description: Tạo thí nghiệm chỉ đổi config (không sửa code) bằng cách sinh configs/exp_<tên>.yaml từ base.yaml, chạy smoke với config đó và ghi vào IDEAS.md. Dùng khi ý tưởng chỉ cần đổi siêu tham số hoặc lựa chọn đã có trong config.
argument-hint: "<tên-ngắn> <key=value ...>  vd: ls01 train.label_smoothing=0.1"
arguments: [name]
---

# New experiment

**Tên:** `$name`. **Toàn bộ tham số:** $ARGUMENTS

1. **Kiểm tra config-only.** Mỗi `key=value` phải là key đã có trong `configs/base.yaml` **và** được code đọc
   (grep tên key trong `src/`). Nếu có key chưa được code hỗ trợ, dừng lại: đây là ý tưởng cần sửa code, đề nghị `/dev-cycle`.
2. **Tạo** `configs/exp_$name.yaml`: copy `configs/base.yaml`, sửa đúng các key được yêu cầu. Thêm 2 dòng comment đầu file:
   giả thuyết và thay đổi so với baseline.
3. **Kiểm tra** bằng `<python venv> -m src.train --smoke --config configs/exp_$name.yaml --ckpt-dir checkpoints/smoke --resume none`.
4. **Ghi** vào `IDEAS.md`: cập nhật ý tưởng tương ứng (hoặc thêm mới) với trạng thái `đã hiện thực (configs/exp_$name.yaml)`.
5. **Commit**: `exp: add configs/exp_$name.yaml`. Không push.
6. **Gợi ý bước tiếp:** `/prepare-train run-<số tiếp theo>-$name configs/exp_$name.yaml`.
