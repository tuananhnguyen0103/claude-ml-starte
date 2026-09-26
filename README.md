# claude-ml-starter

Project mẫu để **học và hướng dẫn Claude Code** qua một bài toán ML thật nhưng nhỏ: train CNN phân loại ảnh CIFAR-10.
Code được viết ở máy cá nhân (không cần GPU), đẩy lên GitHub, rồi train trên **Google Colab / Kaggle**, có resume khi phiên bị ngắt.

Repo đi kèm một bộ harness Claude Code hoàn chỉnh để học theo:

- `CLAUDE.md`: chỉ dẫn dự án cho Claude.
- `.claude/settings.json`: quyền allow/ask/deny và 4 hook.
- `.claude/agents/`: 6 subagent (planner, implementer, test-runner, debugger, code-reviewer, experiment-analyst).
- `.claude/skills/`: 8 skill (`/dev-cycle`, `/prepare-train`, `/fix-remote-error`, `/analyze-runs`, `/new-experiment`,
  `/idea-loop`, `/run-status`, và runbook Colab/Kaggle).

## Bắt đầu

```bash
# 1. Môi trường local (CPU)
python -m venv .venv
.venv\Scripts\python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu   # macOS/Linux: .venv/bin/python
.venv\Scripts\python -m pip install -r requirements-dev.txt

# 2. Kiểm tra: phải thấy "passed" cho mọi test
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m src.train --smoke --ckpt-dir checkpoints/smoke

# 3. Mở Claude Code
claude
```

Sau đó đọc [docs/00-lo-trinh.md](docs/00-lo-trinh.md).

## Tài liệu

| # | Nội dung |
|---|---|
| [00](docs/00-lo-trinh.md) | Lộ trình 5 buổi, bản đồ khái niệm → file |
| [01](docs/01-cai-dat.md) | Cài đặt Claude Code, đăng nhập, mở project |
| [02](docs/02-models-va-modes.md) | Model (Fable/Opus/Sonnet/Haiku), effort, fast mode, permission mode, plan mode |
| [03](docs/03-lenh-va-co-che.md) | `/clear`, `/compact`, `/rewind`, `/resume`… và cơ chế context / checkpoint / session |
| [04](docs/04-harness.md) | Harness: CLAUDE.md, settings, permissions, hooks, MCP |
| [05](docs/05-agents-va-skills.md) | Subagent và skill: xây "đội" cho Claude |
| [06](docs/06-quy-trinh-tu-dong.md) | Quy trình tự động: giao task, chạy, debug, phát triển ý tưởng |
| [07](docs/07-colab-kaggle.md) | Colab/Kaggle, checkpoint, runbook khi phiên bị giới hạn |
| [08](docs/08-demo-colab-git-log.md) | Demo: Colab đẩy log lên branch `runs`, Claude đọc để biết run đang tới đâu |
| [09](docs/09-vscode-colab.md) | Kết nối trực tiếp: Claude Code chạy cell trên GPU Colab qua VS Code |

## Cấu trúc

```
├── CLAUDE.md  PROGRESS.md  EXPERIMENTS.md  IDEAS.md
├── configs/base.yaml              # baseline; thí nghiệm = configs/exp_<tên>.yaml
├── src/train.py                   # train + resume + time budget + metrics
├── src/{data,model,config}.py  src/utils/{checkpoint,env,metrics,hub_sync}.py
├── tests/                         # smoke, resume đúng trọng số, hooks
├── scripts/make_notebooks.py      # sinh notebooks/*.ipynb
├── scripts/compare_runs.py        # so sánh results/<run>/ và runs/<run>/
├── scripts/sync_runs.py           # kéo log từ branch runs (Colab đẩy lên) về runs/
├── notebooks/{colab_train,kaggle_train,vscode_colab}.ipynb
├── results/                       # metrics.csv + summary.json của từng run
└── .claude/{settings.json, hooks/, agents/, skills/, rules/}
```
