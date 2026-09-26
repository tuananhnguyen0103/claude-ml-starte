---
name: prepare-train
description: Chuẩn bị một run train trên Colab/Kaggle, gồm kiểm tra, đăng ký run, tạo tag, push và in cấu hình notebook.
argument-hint: "<run-name> [config]"
arguments: [run, config]
disable-model-invocation: true
allowed-tools: Bash(git tag *) Bash(git status *) Bash(git log *) Bash(git remote *)
---

# Prepare train

**Run:** `$run`. **Config:** `$config` (để trống thì dùng `configs/base.yaml`)

## Trạng thái hiện tại
!`git status --short || true`
!`git remote -v || true`
!`git tag --list "run-*" || true`

## Các bước

1. **Tên run** phải có dạng `run-<số 3 chữ số>-<mô-tả-ngắn>`, ví dụ `run-002-ls01`, và chưa có tag trùng trong danh sách trên.
   Nếu thiếu hoặc sai, đề xuất tên hợp lệ tiếp theo rồi hỏi người dùng.
2. **Working tree sạch.** Nếu còn thay đổi chưa commit, dừng lại và đề nghị `/dev-cycle` hoặc commit trước.
3. **Config tồn tại** và chạy được: giao cho `test-runner` (nêu config). Phải **PASS**, nếu không thì dừng lại.
4. **Remote.** Nếu chưa có `origin`, dừng lại và hướng dẫn tạo repo GitHub (`docs/07-colab-kaggle.md` mục 1).
5. **Đăng ký run**:
   - Thêm dòng vào `EXPERIMENTS.md`: Run, ngày hôm nay, REF = tên run, Config, Thay đổi so với baseline, Trạng thái `chờ chạy`.
   - Cập nhật `PROGRESS.md` mục "Run đang chạy".
   - Commit: `docs: register <run>`.
6. **Tag và push** (git push sẽ hỏi quyền người dùng; đó là thiết kế có chủ đích):
   ```
   git tag -a <run> -m "<config>: <mô tả ngắn>"
   git push origin HEAD
   git push origin <run>
   ```
7. **In hướng dẫn chạy** cho người dùng:
   ```python
   REF      = "<run>"
   RUN_NAME = "<run>"
   CONFIG   = "<config>"
   ```
   - Colab: mở `notebooks/colab_train.ipynb` (File → Open notebook → GitHub), sửa Cell cấu hình, Run all.
   - Kaggle: import `notebooks/kaggle_train.ipynb`, sửa cell cấu hình, *Save Version → Save & Run All*.
   - Xong run: tải `metrics.csv` và `summary.json` về `results/<run>/`, rồi chạy `/analyze-runs`.
