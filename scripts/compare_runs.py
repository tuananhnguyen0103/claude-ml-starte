"""So sánh các run: đọc <thư mục>/<run>/metrics.csv (+ summary.json, progress.json) và in bảng markdown.

Chạy: python scripts/compare_runs.py [thư mục ...]   (mặc định: results và runs)
Chỉ dùng thư viện chuẩn để chạy được bằng bất kỳ Python 3.8+ nào (không cần venv).
"""
import csv
import json
import sys
from pathlib import Path


def load_run(run_dir):
    by_epoch = {}
    metrics = run_dir / "metrics.csv"
    if metrics.exists():
        with metrics.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                by_epoch[int(row["epoch"])] = row      # resume có thể ghi trùng epoch: giữ dòng cuối
    summary_file = run_dir / "summary.json"
    summary = json.loads(summary_file.read_text(encoding="utf-8")) if summary_file.exists() else {}
    return [by_epoch[k] for k in sorted(by_epoch)], summary


def find_runs(roots):
    """Gộp run từ nhiều thư mục; trùng tên thì giữ bản có nhiều epoch hơn."""
    found = {}
    for root in map(Path, roots):
        for p in sorted(root.iterdir()) if root.exists() else []:
            if not ((p / "metrics.csv").exists() or (p / "summary.json").exists()):
                continue
            rows, _ = load_run(p)
            if p.name not in found or len(rows) > len(load_run(found[p.name])[0]):
                found[p.name] = p
    return [found[k] for k in sorted(found)]


def main(*roots):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    roots = roots or ("results", "runs")          # results/: tải tay; runs/: scripts/sync_runs.py kéo từ branch runs
    runs = find_runs(roots)
    if not runs:
        print(f"Chưa có run nào trong {', '.join(r + '/' for r in roots)}. Chạy `python scripts/sync_runs.py` "
              "hoặc tải metrics.csv + summary.json về results/<run>/ trước.")
        return
    print("| run | epoch | best val_acc | val_acc cuối | train_acc cuối | gap train-val | phút GPU | trạng thái |")
    print("|---|---|---|---|---|---|---|---|")
    trends = []
    for run_dir in runs:
        rows, summary = load_run(run_dir)
        if not rows:
            print(f"| {run_dir.name} | - | - | - | - | - | - | chưa có metrics |")
            continue
        last = rows[-1]
        best = max(float(r["val_acc"]) for r in rows)
        gap = float(last["train_acc"]) - float(last["val_acc"])
        progress = run_dir / "progress.json"
        status = "xong" if summary else "đang chạy / bị ngắt"
        if progress.exists():
            status = json.loads(progress.read_text(encoding="utf-8")).get("status", status)
        print(f"| {run_dir.name} | {last['epoch']} | {best:.4f} | {float(last['val_acc']):.4f} | "
              f"{float(last['train_acc']):.4f} | {gap:+.4f} | {last['train_time_min']} | {status} |")
        trends.append((run_dir.name, [r["val_acc"] for r in rows[-5:]]))
    print("\nval_acc 5 epoch cuối:")
    for name, vals in trends:
        print(f"- {name}: {' → '.join(vals)}")


if __name__ == "__main__":
    main(*sys.argv[1:])
