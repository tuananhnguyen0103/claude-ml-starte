# PROGRESS

_Cập nhật: 2026-09-26_

## Đang làm
- Chưa có task. Bước đầu: tạo repo GitHub, push, chạy run baseline (xem README → Bắt đầu).

## Run đang chạy
| RUN_NAME | Nền tảng/GPU | REF (tag) | Checkpoint ở đâu | Tiến độ | Trạng thái |
|---|---|---|---|---|---|

## Bước tiếp theo
1. `/prepare-train run-001-baseline` → chạy notebook Colab hoặc Kaggle.
2. Tải `metrics.csv`, `summary.json` về `results/run-001-baseline/` → `/analyze-runs`.

## Lỗi / ghi chú
- Resume được kiểm chứng bằng `tests/test_train.py::test_resume_gives_same_weights_as_uninterrupted`.
