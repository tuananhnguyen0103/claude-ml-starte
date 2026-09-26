---
name: fix-remote-error
description: Sửa lỗi xảy ra khi train trên Colab/Kaggle dựa trên log người dùng dán vào, rồi hướng dẫn chạy tiếp mà không mất tiến độ.
argument-hint: "[run-name]  (dán log lỗi ngay sau lệnh)"
disable-model-invocation: true
---

# Fix remote error

**Run liên quan:** $ARGUMENTS

1. **Thu thập.** Nếu notebook bật `LOG_BRANCH`, chạy `python scripts/sync_runs.py` rồi đọc `runs/<run>/progress.json`
   (trường `error`) và `runs/<run>/train_tail.log`, không cần người dùng dán gì. Nếu không có log ở đó
   và tin nhắn chưa có log lỗi, yêu cầu người dùng dán đủ các thứ sau: traceback đầy đủ, cell bị lỗi,
   nền tảng (Colab/Kaggle, GPU), giá trị `REF` và `RUN_NAME` trong notebook.
2. **Chẩn đoán**: giao cho subagent `debugger`, kèm nguyên văn log và các thông tin trên.
3. **Nếu là lỗi môi trường hoặc lỗi resume** (không cần sửa code): trình bày hướng dẫn thao tác của debugger. Xong.
4. **Nếu là lỗi code**:
   - `test-runner` phải PASS, sau đó `code-reviewer` không còn BLOCKER.
   - Commit `fix: <mô tả>` và ghi chú lỗi vào `PROGRESS.md`.
   - Hỏi người dùng có push ngay không. Nếu đồng ý:
     - Notebook đang dùng **branch** (`REF = "main"`): push rồi chạy lại cell clone/pull và cell train.
     - Notebook đang dùng **tag** (`REF = "run-00X-..."`): tạo tag mới `<run>b` trỏ vào commit sửa, push tag,
       đổi `REF` sang tag mới và **giữ nguyên `RUN_NAME`** để resume từ checkpoint cũ.
5. **Nhắc** người dùng: không đổi `RUN_NAME` khi muốn train tiếp. Chỉ đổi khi debugger kết luận checkpoint cũ không dùng được.
