---
paths:
  - "src/**/*.py"
  - "tests/**/*.py"
---

# Quy tắc khi sửa code train (chỉ nạp khi Claude làm việc với src/ hoặc tests/)

- Mọi state ảnh hưởng tới việc train tiếp phải nằm trong dict checkpoint ở `save()` của `src/train.py`
  và được khôi phục ở nhánh `if ck:`. Nếu thiếu, resume sẽ khác kết quả chạy một mạch.
- Không tạo RNG ngầm: DataLoader mới phải có `generator=` riêng (xem `src/data.py`). Nếu không, phiên resume tiêu thụ RNG toàn cục
  nhiều hơn chạy một mạch.
- Sau khi sửa luồng train, `tests/test_train.py::test_resume_gives_same_weights_as_uninterrupted` phải còn pass.
- Key config mới đọc bằng `.get(key, default)`, để config cũ và checkpoint cũ vẫn chạy.
- In log bằng `print` với tiền tố dạng `[resume]`, `[ckpt:...]`, `[epoch N/M]` để dễ đọc trên notebook.
