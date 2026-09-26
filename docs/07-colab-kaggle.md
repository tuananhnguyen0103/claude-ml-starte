# 07 · Train trên Colab/Kaggle và xử lý khi phiên bị giới hạn

Máy cá nhân chỉ viết code và chạy smoke test. Việc train chạy trên GPU của Colab hoặc Kaggle.
**GitHub là cầu nối duy nhất cho code; checkpoint không bao giờ đi qua git.**

```
Máy cá nhân (Claude Code) ── push ──► GitHub ── clone/pull tag ──► Colab / Kaggle (GPU)
                                                                     │
                                          checkpoint · metrics ──────┤
                                                                     ▼
                                               Drive / Kaggle Output / HF Hub
```

## 1. Thiết lập một lần

### Repo GitHub
```bash
git init -b main
git add .
git commit -m "chore: khởi tạo project"
# tạo repo trống (private) trên github.com, rồi:
git remote add origin https://github.com/<GH_USER>/<REPO>.git
git push -u origin main
```

### Token cho Colab/Kaggle (repo private)
GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens**:
- Repository access: *Only select repositories*, chọn repo này.
- Permissions → Contents: **Read-only** nếu notebook chỉ cần pull; **Read and write** nếu bật `LOG_BRANCH`
  để Colab đẩy tiến độ lên branch `runs` cho Claude Code đọc (xem [08](08-demo-colab-git-log.md)).
- Expiration: 30–90 ngày.

| Nền tảng | Thêm secret | Tên |
|---|---|---|
| Colab | Thanh trái → 🔑 *Secrets* → Add new secret → bật **Notebook access** | `GITHUB_TOKEN` (và `HF_TOKEN` nếu dùng HF Hub) |
| Kaggle | Trong notebook: *Add-ons → Secrets* → Add → tick gắn vào notebook | như trên |

Kaggle còn cần: *Settings* → Accelerator **GPU**; Internet **On** (tài khoản phải xác minh số điện thoại).

### Notebook
Hai notebook được **sinh** từ `scripts/make_notebooks.py`, nên sửa file `.py` đó rồi chạy lại (hook chặn sửa `.ipynb` trực tiếp).
- Colab: *File → Open notebook → GitHub*, dán URL repo, chọn `notebooks/colab_train.ipynb`.
- Kaggle: *File → Import notebook*, chọn `notebooks/kaggle_train.ipynb`.

Mỗi notebook chỉ có một cell cần sửa, là cell **cấu hình**:

| Biến | Ý nghĩa |
|---|---|
| `REF` | Branch hoặc **tag** code sẽ chạy. Run dài dùng tag do `/prepare-train` tạo: mọi phiên resume chạy đúng cùng code |
| `RUN_NAME` | Tên run. **Giống nhau = train tiếp; khác nhau = run mới** |
| `CONFIG` | File config, ví dụ `configs/exp_ls01.yaml` |
| `CKPT_DIR` | Nơi lưu checkpoint bền vững: Drive (Colab) hoặc `/kaggle/working` (Kaggle) |
| `HF_REPO` | (tùy chọn) repo HF Hub private để resume chéo giữa hai nền tảng |

## 2. Script train hỗ trợ bị ngắt thế nào

`src/train.py` được thiết kế để phiên có thể chết **bất kỳ lúc nào**:

| Cơ chế | Chi tiết |
|---|---|
| Checkpoint theo thời gian | `--save-every-min 20`: mất phiên thì mất tối đa khoảng 20 phút train |
| Checkpoint đầy đủ | model, optimizer, OneCycleLR, AMP scaler, epoch, step, RNG, config, git commit |
| Ghi nguyên tử | Ghi `.tmp` rồi `os.replace`: chết giữa lúc ghi cũng không hỏng checkpoint cũ |
| Resume giữa epoch | Thứ tự batch cố định theo (seed, epoch), nên chỉ cần bỏ qua các batch đã train |
| Time budget | `--time-budget-h 11`: tự lưu và dừng sạch trước giới hạn 12h |
| Cảnh báo lệch code | Checkpoint từ commit khác code hiện tại thì in `[CẢNH BÁO]` |
| Metrics bền vững | `metrics.csv` và `summary.json` nằm cạnh checkpoint |
| Kiểm chứng | `tests/test_train.py`: resume cho **đúng trọng số** như chạy một mạch |

## 3. Các giới hạn thường gặp

> Số liệu tham khảo, các nền tảng thay đổi thường xuyên. Hãy kiểm tra trang chính thức.

| Nền tảng | Giới hạn phiên | Quota | Lưu trữ bền vững |
|---|---|---|---|
| Colab Free | Tối đa khoảng 12h, thường ngắn hơn; ngắt khi không tương tác | GPU cấp động, có lúc hết | Google Drive |
| Colab Pro/Pro+ | Dài hơn; Pro+ chạy nền được | Theo compute units | Google Drive |
| Kaggle | Khoảng 12h/phiên GPU, khoảng 9h TPU | GPU khoảng 30h/tuần | Output của version, Dataset |
| Claude Code | Hạn mức sử dụng theo chu kỳ, và context của mỗi hội thoại | Theo gói | git + `PROGRESS.md` ([03](03-lenh-va-co-che.md) mục 6) |

Không dùng script tự click để giữ phiên Colab (có thể bị hạn chế tài khoản). Hãy dựa vào checkpoint.

## 4. Runbook: các bước khi phiên bị ngắt

### A. Colab bị ngắt (hết giờ, mất mạng, không tương tác)
1. *Runtime → Connect*. Nếu báo hết GPU thì đợi hoặc chuyển Kaggle (bước D).
2. **Không đổi** `RUN_NAME`, `REF`, `CONFIG` trong cell cấu hình.
3. *Runtime → Run all*. Mọi cell đều chạy lại an toàn.
4. Log cell train phải có `[resume] .../step_XXXXXXXX.pt → epoch E, step S/T`. Nếu thấy `[start] train từ đầu` thì dừng lại,
   chạy `!ls -lh {CKPT_DIR}` để kiểm tra Drive đã mount và `RUN_NAME` đúng.
5. Ghi vào `PROGRESS.md` (hoặc nhờ Claude): số lần ngắt, step hiện tại.

### B. Kaggle Interactive bị ngắt
`/kaggle/working` đã mất. Chỉ resume được nếu đã bật `HF_REPO`. Train dài thì dùng chế độ Batch (C).

### C. Kaggle Batch: train qua nhiều phiên nối tiếp
1. Phiên 1: *Save Version → Save & Run All (Commit)*. Run chạy nền, `--time-budget-h 11` giúp nó dừng sạch nên Output được lưu.
2. Phiên 2: mở notebook → *Add Input → Your Work →* chọn **Output của chính notebook này** (version vừa chạy).
   Chạy `!ls /kaggle/input` để xem đường dẫn thật, sửa `PREV_CKPT`.
3. *Save & Run All* lần nữa. Cell khôi phục chép checkpoint, `metrics.csv`, `best.pt` sang `CKPT_DIR`, rồi cell train tự resume.
4. Lặp lại tới khi có `summary.json`. Theo dõi quota GPU còn lại trong tuần.

### D. Chuyển Colab ↔ Kaggle giữa chừng
1. Mang checkpoint sang: đặt `HF_REPO` giống nhau ở hai notebook (script tự push/pull `last.pt`), hoặc tải file `step_*.pt`
   mới nhất từ Drive rồi upload thành Kaggle Dataset (và ngược lại).
2. Giữ **cùng `REF` và `CONFIG`**.
3. GPU khác nhau (T4 khoảng 15GB, P100 16GB): đừng đổi `batch_size` giữa run. Số step đổi sẽ làm OneCycleLR lỗi khi resume.
   Nếu buộc phải đổi thì coi là run mới.

### E. Cần sửa code khi run đang dở
- **Sửa không ảnh hưởng checkpoint** (log, metric, sửa lỗi nhỏ): `/fix-remote-error` → commit → tag mới `run-00X-...b`
  → đổi `REF`, **giữ** `RUN_NAME` → resume.
- **Sửa làm checkpoint không tương thích** (kiến trúc, số lớp, optimizer, epochs, batch size): đặt `RUN_NAME` mới, train lại.

## 5. Sau khi run xong
Nếu bật `LOG_BRANCH`, chỉ cần hỏi Claude *"run xong chưa?"* rồi `/analyze-runs`: log đã có trên branch `runs`
([08](08-demo-colab-git-log.md)). Nếu không bật:

1. Tải `metrics.csv` và `summary.json` từ `MyDrive/ckpt/<RUN_NAME>/` (Colab) hoặc tab Output (Kaggle).
2. Chép vào `results/<RUN_NAME>/` trong repo local.
3. Trong Claude Code: `/analyze-runs` → cập nhật `EXPERIMENTS.md`, thêm ý tưởng vào `IDEAS.md`.
4. Commit kết quả (file text nhỏ, được phép): nhờ Claude *"commit results/run-00X"*.

## 6. Lỗi thường gặp

| Triệu chứng | Nguyên nhân / Cách xử lý |
|---|---|
| `fatal: Authentication failed` | Token hết hạn, chưa bật *Notebook access* (Colab), chưa gắn secret (Kaggle), hoặc token không có quyền với repo |
| Notebook không thấy code mới | Chưa push (`git log origin/main` ở local), hoặc `REF` là tag cũ |
| `ModuleNotFoundError: No module named 'src'` | Cell `%cd {WORK}` chưa chạy; phải chạy `python -m src.train` từ gốc repo |
| Kaggle không clone hoặc không tải CIFAR được | Internet đang Off |
| Train lại từ step 0 | Sai `RUN_NAME`/`CKPT_DIR`, Drive chưa mount, Kaggle chưa khôi phục từ `PREV_CKPT` |
| OneCycleLR báo lỗi khi resume | Đã đổi `train.epochs` hoặc `batch_size`. Trả lại giá trị cũ hoặc dùng `RUN_NAME` mới |
| `CUDA out of memory` | Giảm `batch_size` (là run mới), hoặc dùng model nhỏ hơn |
| Lỗi CUDA sau `pip install` | Có ai thêm torch vào `requirements.txt`. Xóa đi, restart runtime |
| Kaggle Output trống | Run bị kill vì quá giờ. Giảm `--time-budget-h` |
| Đọc data chậm trên Colab | Dữ liệu ở `/content/data` (ổ local) là đúng, đừng đọc thẳng từ Drive |
