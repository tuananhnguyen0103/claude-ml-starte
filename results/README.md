# results/

Kết quả **nhỏ, dạng text** của mỗi run, được commit vào git để phân tích và so sánh:

```
results/
└── run-001-baseline/
    ├── metrics.csv     # mỗi epoch một dòng: loss, acc, lr, thời gian
    └── summary.json    # best val_acc, số epoch, commit, config đầy đủ
```

Cách lấy về sau khi train xong:

- **Colab**: tải từ `MyDrive/ckpt/<RUN_NAME>/` trên Google Drive.
- **Kaggle**: tab *Output* của version notebook → thư mục `ckpt/<RUN_NAME>/`.

Không đặt checkpoint (`*.pt`) ở đây, `.gitignore` sẽ chặn. Sau khi chép file vào, chạy `/analyze-runs` trong Claude Code
hoặc `python scripts/compare_runs.py`.
