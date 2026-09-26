---
name: analyze-runs
description: Phân tích kết quả các run (results/ và runs/ kéo từ branch git runs), so sánh với baseline, cập nhật EXPERIMENTS.md và đề xuất thí nghiệm tiếp theo vào IDEAS.md. Dùng khi người dùng báo đã có kết quả run hoặc hỏi nên thử gì tiếp.
argument-hint: "[run-name ...]"
context: fork
agent: experiment-analyst
background: false
---

Phân tích các run: $ARGUMENTS (để trống thì phân tích mọi run trong `results/` và `runs/`).

Trước tiên chạy `python scripts/sync_runs.py` để kéo log mới nhất từ branch `runs` (nếu có).

Làm theo quy trình trong phần mô tả vai trò của bạn: chạy `python scripts/compare_runs.py`, chẩn đoán từng run,
cập nhật `EXPERIMENTS.md` và `IDEAS.md`, ghi điều học được vào bộ nhớ agent.

Nếu `results/` và `runs/` đều chưa có run nào, trả về hướng dẫn tải `metrics.csv` và `summary.json` từ Drive/Kaggle về `results/<run>/`
(xem `results/README.md`), không bịa kết quả.

Trả về báo cáo tối đa 15 dòng.
