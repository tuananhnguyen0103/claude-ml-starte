---
name: run-status
description: Xem tiến độ các run đang train trên Colab/Kaggle bằng cách kéo log từ branch git `runs` (progress.json, metrics.csv, train_tail.log). Dùng khi người dùng hỏi run đang tới đâu, còn bao lâu, có lỗi không, hay Colab còn chạy không.
argument-hint: "[run-name]"
allowed-tools: Bash(python scripts/sync_runs.py *) Bash(python scripts/compare_runs.py *)
---

# Run status

**Run cần xem:** $ARGUMENTS (trống = mọi run bên dưới)

## Log mới nhất từ branch `runs`
!`python scripts/sync_runs.py || true`

## Cách trả lời
1. Tóm tắt ngắn cho từng run liên quan: trạng thái, epoch/tổng, val_acc mới nhất và best, ETA, cập nhật cách đây bao lâu.
   Cần xu hướng thì đọc `runs/<run>/metrics.csv`.
2. Xử lý theo trạng thái trong `runs/<run>/progress.json`:
   - `running`: bình thường. Nếu bảng có cảnh báo "có thể phiên đã bị ngắt", hướng dẫn resume: mở notebook, *Run all*
     với cùng `RUN_NAME` (`docs/07-colab-kaggle.md` mục 4).
   - `stopped-time-budget`: đã lưu checkpoint và dừng sạch. Hướng dẫn chạy lại notebook với cùng `RUN_NAME`.
   - `interrupted`: người dùng tự dừng trên notebook. Hỏi có muốn chạy tiếp không.
   - `error`: đọc `runs/<run>/train_tail.log` và trường `error`, trích dòng lỗi chính. Giao subagent `debugger`
     chẩn đoán theo quy trình `/fix-remote-error`, **dùng log này thay vì bắt người dùng dán lại**.
   - `done`: báo kết quả cuối và gợi ý `/analyze-runs`.
3. Cập nhật dòng của run trong `PROGRESS.md` mục "Run đang chạy" (tiến độ, trạng thái). Không commit chỉ vì việc này.
4. Nếu script báo chưa có branch `runs`: nhắc kiểm tra `LOG_BRANCH` trong notebook và token có quyền ghi
   (`docs/08-demo-colab-git-log.md` mục 2).
