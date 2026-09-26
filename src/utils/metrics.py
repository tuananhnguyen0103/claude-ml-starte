"""Ghi metrics mỗi epoch ra CSV nằm cạnh checkpoint (Drive / Kaggle Output), để phân tích sau."""
import csv
import os

FIELDS = ["epoch", "step", "train_loss", "train_acc", "val_loss", "val_acc", "lr", "train_time_min", "git_commit"]


def append_metrics(ckpt_dir, row):
    path = os.path.join(ckpt_dir, "metrics.csv")
    new_file = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        w.writerow({k: row.get(k) for k in FIELDS})
    return path
