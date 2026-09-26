# 08 · Demo: Colab đẩy log lên git, Claude Code đọc để biết đang tới đâu

## 0. Cách này có ổn không?

**Ổn, và rất hợp để demo**, miễn là giữ 4 điều kiện. Project đã làm sẵn cả 4:

| Điều kiện | Vì sao | Project làm thế nào |
|---|---|---|
| Đẩy lên **branch riêng `runs`**, không đẩy vào `main` | Đẩy vào `main` sẽ xung đột với code bạn đang sửa, lẫn commit log với commit code, và mỗi `git pull` kéo theo hàng trăm commit log | `--log-branch runs`; mỗi run một thư mục trên branch |
| Chỉ đẩy **file text nhỏ** | Git không dành cho checkpoint hàng chục MB | Chỉ `progress.json`, `metrics.csv`, `summary.json`, 200 dòng log cuối |
| Đẩy **thưa** và **không bao giờ làm hỏng việc train** | Mất mạng hay token hết hạn không được phép giết một run 10 giờ | Mỗi N phút (`LOG_EVERY_MIN`) và luôn đẩy khi dừng/lỗi; git lỗi chỉ in cảnh báo, 3 lần liên tiếp thì tự tắt |
| Token **có quyền ghi nhưng giới hạn chặt** | Token ghi rủi ro hơn token chỉ đọc | Fine-grained, chỉ repo này, hạn ngắn (mục 2); nâng cao: repo log riêng (mục 6) |

Hai điều cần hiểu đúng:
- **Claude Code không điều khiển Colab trực tiếp.** Git là kênh trung gian hai chiều: *code đi xuống* qua tag/branch,
  *log đi lên* qua branch `runs`. Bạn vẫn là người bấm *Run all* trên Colab.
- **Không phải realtime.** Claude thấy trạng thái tại lần đẩy gần nhất. Nếu Colab chết đột ngột (ngắt kết nối, hết giờ),
  sẽ không có lần đẩy cuối. Khi đó `updated_at` cũ dần, và `sync_runs.py` cảnh báo "có thể phiên đã bị ngắt".

## 1. Luồng hoạt động

```
  MÁY CÁ NHÂN                              GITHUB                           GOOGLE COLAB (GPU)
  ───────────                              ──────                           ─────────────────
  Claude Code ── push code/tag ──────────► main, tag run-001 ── clone ────► notebook: python -m src.train
                                                                              --log-branch runs
                                                                              │ mỗi N phút / khi dừng / khi lỗi
  /run-status                              branch "runs"  ◄── git push ─────┘ (progress.json, metrics.csv,
   └─ scripts/sync_runs.py ◄── git fetch ─ run-001/...                          summary.json, train_tail.log)
       → runs/run-001/ (gitignored)
       → bảng tiến độ + cảnh báo
   └─ Claude đọc, tóm tắt, gợi ý bước tiếp (resume / debug / analyze)
```

Các thành phần:

| File | Vai trò |
|---|---|
| `src/utils/run_logger.py` | Chạy trên Colab: ghi `progress.json`, chép log vào `train.log`, commit và push lên branch `runs` trong một thư mục git riêng (`/tmp/runlog-<run>`) nên không đụng vào code đang chạy |
| `src/train.py` | Gọi logger lúc bắt đầu, cuối epoch, khi dừng vì time budget, khi xong, và khi **crash** (đẩy cả traceback) |
| `scripts/sync_runs.py` | Chạy ở local: `git fetch` branch `runs` rồi đọc file bằng `git show`, **không đổi branch đang làm**; chép vào `runs/` và in bảng |
| `.claude/skills/run-status/` | Skill Claude **tự gọi** khi bạn hỏi "run đang tới đâu?" |

## 2. Chuẩn bị (làm một lần)

1. **Repo đã lên GitHub** (`docs/07-colab-kaggle.md` mục 1) và bạn đã mở `claude` ở chế độ tương tác một lần trong thư mục project để chấp nhận workspace trust.
2. **Token có quyền ghi.** GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens:
   - Repository access: *Only select repositories*, chỉ chọn repo này.
   - Permissions → **Contents: Read and write**.
   - Expiration: 7–30 ngày cho demo.
3. **Colab:** 🔑 Secrets → `GITHUB_TOKEN` = token trên, bật *Notebook access*.

Token nằm trong `~/.git-credentials` của máy ảo Colab, không nằm trong URL hay log. Logger đặt `GIT_TERMINAL_PROMPT=0`,
nên nếu thiếu token nó báo lỗi ngay thay vì treo chờ nhập mật khẩu.

## 3. Kịch bản demo (khoảng 15 phút)

### Bước 1. Đẩy code (local, trong Claude Code)
```
> /prepare-train run-001-demo
```
Hoặc nhanh hơn cho demo: *"commit và push lên main"* rồi để `REF = "main"` trong notebook.

### Bước 2. Chạy trên Colab
Mở `notebooks/colab_train.ipynb` (*File → Open notebook → GitHub*), chọn runtime **T4 GPU**, sửa cell cấu hình:
```python
REF           = "run-001-demo"      # hoặc "main"
RUN_NAME      = "run-001-demo"
LOG_BRANCH    = "runs"
LOG_EVERY_MIN = 1                   # demo: đẩy dày để thấy thay đổi nhanh
EXTRA_ARGS    = "--set train.epochs=10"   # rút ngắn run cho demo
```
*Runtime → Run all.* Trong output của cell train phải có dòng:
```
[runlog] đẩy tiến độ lên branch 'runs' mỗi 1 phút
```
Tùy chọn: mở GitHub, chuyển sang branch `runs` để khán giả thấy thư mục `run-001-demo/` xuất hiện và được cập nhật.

### Bước 3. Hỏi Claude (local)
```
> run-001-demo đang tới đâu rồi?
```
Claude tự nạp skill `run-status`. Skill chạy `python scripts/sync_runs.py` và Claude trả lời dựa trên bảng, ví dụ (minh họa):
```
| run | trạng thái | epoch | val_acc | best | ETA (phút) | cập nhật | nền tảng / GPU |
|---|---|---|---|---|---|---|---|
| run-001-demo | running | 4/10 | 0.7312 | 0.7312 | 3.1 | 0 phút trước | colab / Tesla T4 |
```
Có thể hỏi tiếp: *"val_acc có đang tăng đều không?"*. Claude đọc `runs/run-001-demo/metrics.csv` để trả lời.

### Bước 4. Ngắt thử
Trên Colab: *Runtime → Interrupt execution*. Logger bắt `KeyboardInterrupt` và đẩy trạng thái `interrupted`.
```
> run-001-demo sao rồi?
```
Claude báo run đã bị dừng tay ở epoch X và hướng dẫn chạy lại. Bạn *Run all* với cùng `RUN_NAME`,
log in `[resume] ... → epoch X`. Hỏi Claude lần nữa để thấy trạng thái quay về `running`.

> Nếu thay vì Interrupt, bạn **đóng hẳn runtime** (*Runtime → Disconnect and delete runtime*), sẽ không có lần đẩy cuối.
> Sau khoảng `2 × LOG_EVERY_MIN + 10` phút, `sync_runs.py` sẽ cảnh báo "có thể phiên đã bị ngắt". Đây là ví dụ tốt về giới hạn "không realtime".

### Bước 5. Crash thử: Claude đọc traceback mà bạn không cần dán
Đổi `RUN_NAME = "run-002-crash"` và `EXTRA_ARGS = "--set model.name=vgg"` (model không tồn tại), rồi *Run all*.
```
> run-002-crash bị gì vậy?
```
Trạng thái là `error`. Claude đọc `runs/run-002-crash/train_tail.log`, trích dòng
`ValueError: Model không hỗ trợ: 'vgg' (có: small_cnn, resnet18)` và kết luận đây là lỗi cấu hình, không cần sửa code.
Với lỗi code thật, Claude giao `debugger` xử lý theo quy trình `/fix-remote-error`.

### Bước 6. Kết thúc
Khi `run-001-demo` báo `done`:
```
> /analyze-runs
```
`compare_runs.py` đọc cả `runs/` (từ branch) và `results/` (tải tay), rồi `experiment-analyst` cập nhật `EXPERIMENTS.md` và `IDEAS.md`.

### Bonus: để Claude tự theo dõi
```
> /loop 5m /run-status run-001-demo
```
Claude kiểm tra mỗi 5 phút khi phiên còn mở, báo khi xong hoặc khi có lỗi. Dừng bằng `Esc` hoặc đóng phiên.

## 4. Trên branch `runs` có gì

```
runs (branch)
├── run-001-demo/
│   ├── progress.json      ← Claude đọc cái này trước tiên
│   ├── metrics.csv
│   ├── summary.json       (khi xong)
│   └── train_tail.log     (200 dòng log cuối, có traceback nếu lỗi)
└── run-002-crash/ ...
```
`progress.json` (ví dụ):
```json
{
  "run_name": "run-001-demo", "status": "running", "push_every_min": 1,
  "platform": "colab", "gpu": "Tesla T4", "config": "configs/base.yaml", "git_commit": "a1b2c3d",
  "epoch": 4, "total_epochs": 10, "step": 1560, "total_steps": 3900,
  "val_acc": 0.7312, "best_val_acc": 0.7312, "train_time_min": 2.4, "eta_min": 3.1,
  "updated_at": "2026-09-26T08:15:02+00:00"
}
```
Trạng thái có thể là: `running`, `stopped-time-budget`, `interrupted`, `error`, `done`.

## 5. Cơ chế an toàn trong logger
- Mọi lệnh git có timeout. Lỗi chỉ in `[runlog] không đẩy được log (1/3)`; 3 lần liên tiếp thì tắt đẩy log cho phiên đó. **Việc train không bao giờ dừng vì logger.**
- Push bị từ chối (một run khác vừa đẩy lên cùng branch): logger lấy bản mới nhất, commit lại file của mình rồi đẩy lại.
  Mỗi run ghi vào thư mục riêng nên không có xung đột.
- Thư mục git của logger (`/tmp/runlog-<run>`) tách khỏi thư mục code, nên code đang checkout theo tag không bị ảnh hưởng.
- Không bật `--log-branch` thì logger là `NullLogger`: hành vi giống hệt trước khi có tính năng này.
- Kiểm chứng bằng `tests/test_run_logger.py`: dùng một bare repo local đóng vai GitHub, test đẩy log, dừng rồi resume,
  crash có traceback, hai run đẩy cùng lúc, remote hỏng không làm hỏng train, và `sync_runs.py`.

## 6. Nâng cao và các phương án khác
- **Tách repo log** để token không đụng được repo code: tạo repo `<REPO>-runs`, token chỉ cấp quyền ghi cho repo đó,
  rồi chạy train với `EXTRA_ARGS="--log-remote https://github.com/<user>/<REPO>-runs.git"`.
  Ở local: `git remote add runs-origin <url>` và `python scripts/sync_runs.py --remote runs-origin`.
- **Bảo vệ `main`** bằng branch protection/rulesets nếu gói GitHub của bạn hỗ trợ cho repo private.
- **Dọn dẹp:** branch `runs` chỉ chứa text nên tăng rất chậm. Muốn làm lại từ đầu thì xóa branch trên GitHub.
- **So với W&B/TensorBoard:** chúng realtime và có biểu đồ đẹp cho *người* xem, nhưng Claude cần API hoặc MCP mới đọc được.
  Branch git là cách đơn giản nhất để *Claude* đọc, vì không cần thêm công cụ hay tài khoản nào. Hai cách dùng song song được.
- **Kaggle:** notebook Kaggle có cùng cell cấu hình (`LOG_BRANCH`...). Chế độ *Save & Run All* chạy nền nên càng hợp,
  vì bạn đóng trình duyệt vẫn hỏi Claude được run đang tới đâu.
