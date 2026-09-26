---
name: colab-kaggle-runbook
description: Kiến thức vận hành train trên Google Colab và Kaggle, gồm setup notebook, secrets, resume khi phiên bị ngắt hoặc hết quota, chuyển nền tảng và lỗi thường gặp. Dùng khi người dùng hỏi về Colab/Kaggle, phiên bị ngắt, resume, GPU, hoặc dán lỗi từ notebook.
---

# Runbook Colab / Kaggle

Chi tiết đầy đủ ở `docs/07-colab-kaggle.md`. Dưới đây là phần cần nhớ.

## Nguyên tắc
- Git chỉ chứa code. Checkpoint nằm ở Drive (`MyDrive/ckpt/<RUN_NAME>`), Kaggle Output (`/kaggle/working/ckpt/<RUN_NAME>`),
  hoặc HF Hub (`--hub-repo`).
- `RUN_NAME` giống nhau nghĩa là train tiếp, khác nhau nghĩa là run mới. `REF` là tag do `/prepare-train` tạo để code không đổi giữa các phiên.
- `--time-budget-h 11` < giới hạn 12h, nên script tự lưu và dừng sạch (quan trọng với Kaggle batch: bị kill có thể mất Output).

## Khi phiên bị ngắt
- **Colab**: Reconnect, rồi *Run all*, giữ nguyên Cell cấu hình. Log phải có `[resume] ... → epoch E, step S`.
- **Kaggle Interactive**: `/kaggle/working` đã mất. Chỉ resume được nếu có `--hub-repo`. Train dài nên dùng chế độ Batch.
- **Kaggle Batch**: *Add Input → Your Work →* Output version trước, sửa `PREV_CKPT` (kiểm tra bằng `!ls /kaggle/input`),
  rồi *Save & Run All* lại.
- **Chuyển Colab ↔ Kaggle**: dùng `--hub-repo` (hoặc tải ckpt từ Drive lên thành Kaggle Dataset), giữ cùng `REF` và `CONFIG`.
- **Hết quota GPU Colab**: chuyển Kaggle (khoảng 30h GPU/tuần, con số thay đổi theo thời gian) hoặc đợi.

## Lỗi thường gặp
| Triệu chứng | Xử lý |
|---|---|
| `Authentication failed` khi clone | Secret `GITHUB_TOKEN` hết hạn, chưa bật Notebook access (Colab), chưa gắn secret (Kaggle) |
| Kaggle không clone/tải CIFAR được | Settings → Internet **On** (cần xác minh số điện thoại) |
| Train lại từ step 0 | Sai `RUN_NAME`/`CKPT_DIR`, Drive chưa mount, Kaggle chưa khôi phục từ `PREV_CKPT` |
| `CUDA out of memory` | Giảm `train.batch_size` (qua `--set`), nhưng đó là run mới vì số step thay đổi |
| OneCycleLR báo lỗi số step khi resume | Đã đổi `train.epochs`/`batch_size` giữa chừng. Giữ config cũ hoặc tạo `RUN_NAME` mới |
| `Weights only load failed` | Checkpoint không do project này tạo, hoặc code cũ. `load_ckpt` đã dùng `weights_only=False` |
| Lỗi CUDA sau `pip install` | Có ai thêm torch vào `requirements.txt`. Xóa đi, restart runtime |
| Kaggle Output trống | Run bị kill vì quá giờ. Giảm `--time-budget-h` |
