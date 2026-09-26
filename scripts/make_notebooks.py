"""Sinh notebooks/{colab_train,kaggle_train,vscode_colab}.ipynb từ danh sách cell bên dưới.

Sửa notebook = sửa file này rồi chạy lại: python scripts/make_notebooks.py
(Để Claude sửa file .py dễ và review được hơn nhiều so với sửa JSON của .ipynb.)
"""
import json
import sys
from pathlib import Path

CLONE = '''WORK = {work}
if not os.path.isdir(WORK):
    !git clone -q https://github.com/{{GH_USER}}/{{REPO}}.git {{WORK}}
%cd {{WORK}}
!git fetch -q origin --tags
!git checkout -q {{REF}}
!git reset -q --hard origin/{{REF}} 2>/dev/null || true   # REF là branch → đồng bộ với remote
!git log -1 --oneline'''

CREDENTIALS = '''try:
    token = {get_secret}
    cred = pathlib.Path.home() / ".git-credentials"          # token không nằm trong URL hay log
    cred.write_text(f"https://{{GH_USER}}:{{token}}@github.com\\n")
    cred.chmod(0o600)
    !git config --global credential.helper store
except Exception:
    print("Không đọc được secret GITHUB_TOKEN → chỉ clone được repo public")'''

TRAIN = '''hub = f"--hub-repo {{HF_REPO}}" if HF_REPO else ""
log = f"--log-branch {{LOG_BRANCH}} --log-every-min {{LOG_EVERY_MIN}}" if LOG_BRANCH else ""
!python -m src.train --config {{CONFIG}} --run-name {{RUN_NAME}} --data-dir {data_dir} --ckpt-dir {{CKPT_DIR}} --resume auto --time-budget-h 11 --save-every-min 20 {{hub}} {{log}} {{EXTRA_ARGS}}'''

LOG_CONFIG = '''
LOG_BRANCH    = "runs"   # đẩy tiến độ lên branch này để Claude Code đọc; "" = tắt (token cần quyền GHI)
LOG_EVERY_MIN = 5        # đẩy log tối đa mỗi N phút; demo đặt 1
EXTRA_ARGS    = ""       # tham số thêm cho src.train, vd "--set train.epochs=10"'''

SHOW = '''!tail -n 5 {CKPT_DIR}/metrics.csv
!cat {CKPT_DIR}/summary.json 2>/dev/null || echo "Run chưa xong (chưa có summary.json)"'''

COLAB = [
    ("markdown", """# Train CIFAR-10 trên Google Colab

1. *Runtime → Change runtime type → T4 GPU*.
2. Thêm secret `GITHUB_TOKEN` (biểu tượng 🔑 bên trái, bật **Notebook access**). Token cần quyền **đọc** để clone
   repo private, và quyền **ghi** nếu bật `LOG_BRANCH` (đẩy tiến độ lên branch `runs` cho Claude Code đọc).
3. Sửa Cell cấu hình rồi *Runtime → Run all*.

**Bị ngắt phiên?** Kết nối lại rồi *Run all*, **giữ nguyên `RUN_NAME`**. Script tự train tiếp từ checkpoint trên Drive."""),
    ("code", '''# === Cấu hình (chỉ sửa cell này) ===
GH_USER  = "<GH_USER>"
REPO     = "<REPO>"
REF      = "main"                # branch hoặc tag; run dài nên dùng tag do /prepare-train tạo
RUN_NAME = "run-001-baseline"    # GIỮ NGUYÊN khi resume
CONFIG   = "configs/base.yaml"
CKPT_DIR = f"/content/drive/MyDrive/ckpt/{RUN_NAME}"
HF_REPO  = ""                    # (tùy chọn) "user/cifar-ckpt" để resume chéo sang Kaggle''' + LOG_CONFIG),
    ("code", '''from google.colab import drive
drive.mount("/content/drive")
!nvidia-smi --query-gpu=name,memory.total --format=csv'''),
    ("code", "import os, pathlib\nfrom google.colab import userdata\n\n"
             + CREDENTIALS.format(get_secret='userdata.get("GITHUB_TOKEN")') + "\n\n"
             + CLONE.format(work='f"/content/{REPO}"')),
    ("code", "!pip install -q -r requirements.txt"),
    ("code", '''if HF_REPO:
    os.environ["HF_TOKEN"] = userdata.get("HF_TOKEN")'''),
    ("code", TRAIN.format(data_dir="/content/data")),
    ("code", SHOW),
    ("markdown", """Theo dõi từ máy local: trong Claude Code hỏi *"run đang tới đâu?"* (skill `/run-status` kéo branch `runs`).
Không bật `LOG_BRANCH` thì tải `metrics.csv`, `summary.json` từ `MyDrive/ckpt/<RUN_NAME>/` về `results/<RUN_NAME>/`."""),
]

KAGGLE = [
    ("markdown", """# Train CIFAR-10 trên Kaggle

1. *Settings*: Accelerator **GPU T4 x2** hoặc **P100**; Internet **On** (tài khoản cần xác minh số điện thoại).
2. *Add-ons → Secrets*: thêm `GITHUB_TOKEN` và gắn vào notebook (cần quyền ghi nếu bật `LOG_BRANCH`).
3. Train dài: *Save Version → Save & Run All (Commit)*: chạy nền, đóng trình duyệt vẫn chạy.

**Phiên sau (resume):** *Add Input → Your Work →* chọn Output của version trước, sửa `PREV_CKPT`, rồi Save & Run All lại."""),
    ("code", '''# === Cấu hình (chỉ sửa cell này) ===
GH_USER   = "<GH_USER>"
REPO      = "<REPO>"
REF       = "main"
RUN_NAME  = "run-001-baseline"   # GIỮ NGUYÊN khi resume
CONFIG    = "configs/base.yaml"
CKPT_DIR  = f"/kaggle/working/ckpt/{RUN_NAME}"
PREV_CKPT = f"/kaggle/input/<ten-notebook>/ckpt/{RUN_NAME}"   # kiểm tra đường dẫn thật bằng !ls /kaggle/input
HF_REPO   = ""''' + LOG_CONFIG),
    ("code", "!nvidia-smi --query-gpu=name,memory.total --format=csv"),
    ("code", "import os, pathlib\nfrom kaggle_secrets import UserSecretsClient\n\n"
             + CREDENTIALS.format(get_secret='UserSecretsClient().get_secret("GITHUB_TOKEN")') + "\n\n"
             + CLONE.format(work='f"/tmp/{REPO}"   # ngoài /kaggle/working: Output chỉ chứa kết quả')),
    ("code", "!pip install -q -r requirements.txt"),
    ("code", '''# Khôi phục checkpoint từ Output của version trước (nếu có)
import glob, shutil
os.makedirs(CKPT_DIR, exist_ok=True)
prev = sorted(glob.glob(f"{PREV_CKPT}/step_*.pt"))
if prev and not glob.glob(f"{CKPT_DIR}/step_*.pt"):
    for f in [prev[-1]] + glob.glob(f"{PREV_CKPT}/metrics.csv") + glob.glob(f"{PREV_CKPT}/best.pt"):
        shutil.copy(f, CKPT_DIR)
    print("Đã khôi phục", prev[-1])
else:
    print("Không có checkpoint cũ → train từ đầu" if not prev else "CKPT_DIR đã có checkpoint")'''),
    ("code", '''if HF_REPO:
    os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")'''),
    ("code", TRAIN.format(data_dir="/tmp/data")),
    ("code", SHOW),
]


VSCODE = [
    ("markdown", """# Colab ngay trong VS Code: Claude Code chạy cell trên GPU Colab

1. Góc trên phải: **Select Kernel → Colab → New Colab Server** (chọn GPU T4) → đăng nhập Google.
2. Explorer: chuột phải `src/`, `configs/`, `requirements.txt` → **Upload to Colab**.
3. Giữ notebook này là tab đang mở, rồi nói với Claude Code: *"Chạy trong notebook đang mở: ..."*.
   Mỗi lần Claude muốn chạy code, VS Code hỏi **Execute / Cancel**.
4. Xong việc: Command Palette → **Colab: Remove Server** để trả GPU (tiết kiệm quota).

Hướng dẫn đầy đủ: `docs/09-vscode-colab.md`."""),
    ("code", '''# Kiểm tra GPU của Colab server
!nvidia-smi --query-gpu=name,memory.total --format=csv
import torch
print("torch", torch.__version__, "| cuda:", torch.cuda.is_available())'''),
    ("code", '''# Kiểm tra code đã upload lên /content
%cd /content
import os
missing = [p for p in ("src", "configs", "requirements.txt") if not os.path.exists(p)]
print(f"Thiếu {missing}: chuột phải trong Explorer → Upload to Colab" if missing else "Code đã sẵn sàng")'''),
    ("code", '''# Train ngắn để demo (2 epoch). Checkpoint ở /content/ckpt: mất khi server bị xóa
!pip install -q -r requirements.txt
!python -m src.train --run-name vscode-demo --data-dir /content/data --ckpt-dir /content/ckpt/vscode-demo --set train.epochs=2'''),
    ("code", '''# Train dài: chạy nền để cell trả về ngay, rồi xem tiến độ bằng cell dưới
!nohup python -m src.train --run-name vscode-long --data-dir /content/data --ckpt-dir /content/ckpt/vscode-long > /content/train.log 2>&1 &'''),
    ("code", "!tail -n 5 /content/train.log"),
]


def to_notebook(cells, metadata):
    def lines(src):
        parts = src.split("\n")
        return [p + "\n" for p in parts[:-1]] + [parts[-1]]

    return {
        "nbformat": 4, "nbformat_minor": 4, "metadata": metadata,
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": lines(src)} if kind == "markdown" else
            {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": lines(src)}
            for kind, src in cells
        ],
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    out = Path(__file__).resolve().parent.parent / "notebooks"
    out.mkdir(exist_ok=True)
    kernel = {"name": "python3", "display_name": "Python 3", "language": "python"}
    for name, cells, meta in [
        ("colab_train.ipynb", COLAB, {"kernelspec": kernel, "accelerator": "GPU", "colab": {"provenance": []}}),
        ("kaggle_train.ipynb", KAGGLE, {"kernelspec": kernel}),
        ("vscode_colab.ipynb", VSCODE, {"kernelspec": kernel}),
    ]:
        path = out / name
        path.write_text(json.dumps(to_notebook(cells, meta), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("Đã ghi", path)


if __name__ == "__main__":
    main()
