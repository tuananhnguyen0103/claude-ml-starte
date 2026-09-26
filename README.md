# claude-ml-starter

Project mẫu để **học Claude Code qua một bài toán Machine Learning thật**: train mạng CNN phân loại ảnh CIFAR-10.

Nhiều bạn không có GPU ở nhà. Project này dạy cách làm việc chuyên nghiệp trong điều kiện đó:

- viết code ở máy cá nhân cùng Claude Code, không cần GPU;
- quản lý code bằng Git/GitHub;
- train trên GPU miễn phí của **Google Colab / Kaggle**;
- vẫn train tiếp được khi phiên Colab bị ngắt;
- để Claude tự lập kế hoạch, viết code, test, debug và theo dõi tiến trình train.

> Kết quả thật khi chạy thử: 2 epoch trên Colab T4 đạt **val_acc 73.4%** trong 0.7 phút train.

## Bạn sẽ học được gì

| Chủ đề | Tài liệu |
|---|---|
| Cài đặt Claude Code, đăng nhập, mở project | [docs/01](docs/01-cai-dat.md) |
| Chọn model (Fable / Opus / Sonnet / Haiku), effort, fast mode, chế độ quyền, plan mode | [docs/02](docs/02-models-va-modes.md) |
| Các lệnh `/clear`, `/compact`, `/rewind`, `/resume`… và cơ chế context, checkpoint, session | [docs/03](docs/03-lenh-va-co-che.md) |
| "Harness": `CLAUDE.md`, permissions, hooks, MCP | [docs/04](docs/04-harness.md) |
| Subagent và skill: xây một "đội" AI chia vai | [docs/05](docs/05-agents-va-skills.md) |
| Quy trình tự động: plan, code, test, debug, review, commit | [docs/06](docs/06-quy-trinh-tu-dong.md) |
| Train trên Colab/Kaggle, xử lý khi phiên bị giới hạn | [docs/07](docs/07-colab-kaggle.md) |
| Colab đẩy log lên Git, Claude đọc để biết run đang tới đâu | [docs/08](docs/08-demo-colab-git-log.md) |
| Nối thẳng VS Code với Colab, Claude chạy cell trên GPU | [docs/09](docs/09-vscode-colab.md) |

**Bắt đầu từ [docs/00-lo-trinh.md](docs/00-lo-trinh.md)**: lộ trình 5 buổi, mỗi buổi có mục tiêu, thao tác và bài tập.

## Chuẩn bị

- Python 3.10+ và Git (Windows: cài [Git for Windows](https://git-scm.com/downloads/win)).
- Tài khoản **Claude Pro/Max/Team/Enterprise** hoặc Claude Console để dùng Claude Code
  ([hướng dẫn cài](docs/01-cai-dat.md)).
- Tài khoản Google để dùng Colab (gói miễn phí là đủ).
- Không cần GPU ở máy cá nhân.

## Bắt đầu nhanh (khoảng 10 phút)

```bash
# 1. Lấy code
git clone https://github.com/tuananhnguyen0103/claude-ml-starte.git
cd claude-ml-starte

# 2. Tạo môi trường Python (bản PyTorch CPU, nhẹ)
python -m venv .venv
# Windows:
.venv\Scripts\python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
.venv\Scripts\python -m pip install -r requirements-dev.txt
# macOS/Linux: thay ".venv\Scripts\python" bằng ".venv/bin/python"

# 3. Kiểm tra: mọi test phải "passed"
.venv\Scripts\python -m pytest -q

# 4. Chạy thử train trên CPU với dữ liệu giả (vài giây)
.venv\Scripts\python -m src.train --smoke --ckpt-dir checkpoints/smoke

# 5. Mở Claude Code trong thư mục project
claude
```

Lần đầu mở, Claude Code hỏi bạn có tin tưởng thư mục không. Project có **hooks** (script tự chạy), nên hãy đọc qua
`.claude/settings.json` trước khi đồng ý. Đó là thói quen tốt với mọi repo lạ.

Hooks gọi lệnh `python`. Trên macOS/Linux nếu chỉ có `python3`, sửa `python` thành `python3` trong `.claude/settings.json`.

## Thử ngay với Claude Code

Sau khi mở `claude`, gõ thử:

| Gõ | Điều xảy ra |
|---|---|
| `Giải thích cơ chế resume trong src/train.py` | Claude đọc code và giải thích |
| `/new-experiment ls01 train.label_smoothing=0.1` | Tạo thí nghiệm mới chỉ đổi config, chạy thử rồi commit |
| `/dev-cycle Thêm Mixup vào vòng train, mặc định tắt, có test` | Cả đội subagent làm trọn vòng: plan → code → test → debug → review → commit |
| `@agent-code-reviewer xem thay đổi hiện tại` | Gọi đích danh subagent review |
| `run đang tới đâu rồi?` | Kéo log từ branch `runs` và báo tiến độ train trên Colab |

## Train trên GPU

**Cách A: Colab trên trình duyệt (khuyên dùng cho run dài).** Mở `notebooks/colab_train.ipynb` trên Colab
(*File → Open notebook → GitHub*), sửa `RUN_NAME` trong cell cấu hình rồi *Run all* (repo public nên không cần token; fork thì đổi `GH_USER`).
Bị ngắt phiên thì *Run all* lại với cùng `RUN_NAME`: script tự train tiếp từ checkpoint. Chi tiết: [docs/07](docs/07-colab-kaggle.md).

**Cách B: Kaggle.** Import `notebooks/kaggle_train.ipynb`, bật GPU và Internet, rồi *Save & Run All*.

**Cách C: Colab ngay trong VS Code.** Cài extension *Google Colab*, mở `notebooks/vscode_colab.ipynb`,
chọn *Select Kernel → Colab*. Claude Code có thể chèn và chạy cell trên GPU Colab (mỗi lần chạy bạn bấm Execute).
Chi tiết: [docs/09](docs/09-vscode-colab.md).

## Trong repo có gì

```
├── README.md                      # file này
├── CLAUDE.md                      # chỉ dẫn dự án cho Claude (đọc để hiểu Claude được "dặn" gì)
├── PROGRESS.md  EXPERIMENTS.md  IDEAS.md   # tiến độ, nhật ký thí nghiệm, backlog ý tưởng
├── docs/                          # tài liệu 00–09
├── configs/base.yaml              # cấu hình baseline; thí nghiệm = configs/exp_<tên>.yaml
├── src/
│   ├── train.py                   # train + resume + time budget + metrics + đẩy log lên git
│   ├── data.py  model.py  config.py
│   └── utils/                     # checkpoint, env, metrics, run_logger, hub_sync
├── tests/                         # smoke test, resume ra đúng trọng số, hooks, run_logger
├── scripts/
│   ├── make_notebooks.py          # sinh notebooks/*.ipynb (sửa file này, đừng sửa .ipynb)
│   ├── sync_runs.py               # kéo log từ branch runs về máy
│   └── compare_runs.py            # so sánh kết quả các run
├── notebooks/                     # colab_train, kaggle_train, vscode_colab
├── results/                       # metrics.csv + summary.json của từng run
└── .claude/
    ├── settings.json              # quyền allow/ask/deny + 4 hook
    ├── hooks/                     # chặn force push, chặn commit checkpoint/secret, kiểm tra cú pháp, nạp bối cảnh
    ├── agents/                    # 6 subagent: planner, implementer, test-runner, debugger, code-reviewer, experiment-analyst
    ├── skills/                    # 8 skill: /dev-cycle, /prepare-train, /run-status, /analyze-runs, ...
    └── rules/                     # quy tắc chỉ nạp khi Claude sửa code train
```

## Nguyên tắc của project

1. **Git chỉ chứa code và file text nhỏ.** Checkpoint và dữ liệu nằm ở Drive/Kaggle/HF Hub. Hook tự chặn nếu lỡ commit.
2. **Mọi lần train đều resume được.** Có test chứng minh: train bị ngắt rồi chạy tiếp cho ra đúng trọng số như chạy một mạch.
3. **Cho Claude cách tự kiểm chứng.** Có test chạy vài giây trên CPU, nên Claude tự sửa tới khi pass.
4. **Con người giữ quyết định quan trọng.** Push, dùng GPU và chọn hướng thí nghiệm luôn chờ bạn duyệt.

## Câu hỏi thường gặp

**Không có tài khoản Claude trả phí thì dùng được không?**
Phần ML (`src/`, notebook Colab/Kaggle) chạy bình thường không cần Claude. Phần `.claude/` và `docs/` là để học Claude Code,
cần tài khoản Pro trở lên hoặc Claude Console.

**Máy yếu có chạy được không?**
Được. Máy cá nhân chỉ chạy test và smoke trên CPU với dữ liệu giả. Train thật chạy trên Colab/Kaggle.

**Tôi muốn dùng cho bài toán của mình?**
Fork repo, thay `src/data.py` và `src/model.py`, sửa `configs/base.yaml`, cập nhật `CLAUDE.md`.
Giữ nguyên cơ chế checkpoint/resume và các test, vì chúng là "lưới an toàn" để Claude làm việc tự động.

**Test fail sau khi tôi sửa code?**
Nhờ Claude: *"Test đang fail, dùng subagent debugger tìm nguyên nhân và sửa"*.

## Đóng góp

Gặp lỗi hoặc muốn bổ sung bài tập, hãy mở Issue hoặc Pull Request. Trước khi gửi PR, chạy `python -m pytest -q` và đảm bảo mọi test pass.
