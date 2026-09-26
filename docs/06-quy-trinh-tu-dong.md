# 06 · Quy trình tự động có kiểm soát

Mục tiêu: Claude **tự** giao việc, chạy, debug và phát triển ý tưởng, nhưng trong khuôn khổ rõ ràng.
Con người chỉ giữ các quyết định quan trọng: duyệt kế hoạch lớn, push, dùng GPU, chọn hướng thí nghiệm.

## 1. Bức tranh toàn cảnh

```
            ┌───────────────────────── MÁY CÁ NHÂN (Claude Code) ─────────────────────────┐
            │                                                                             │
 IDEAS.md ──┼─► /idea-loop ──► chọn ý tưởng ──┬─ config-only ─► /new-experiment            │
   ▲        │                                  └─ sửa code ────► /dev-cycle                │
   │        │                                                     │                       │
   │        │      planner ─► implementer ─► test-runner ─┬─ PASS ─► code-reviewer ─► commit
   │        │                      ▲                      └─ FAIL ─► debugger ─┐ (≤ 3 vòng)│
   │        │                      └─────────────────────────────────────────────┘         │
   │        │                                                                             │
   │        │  /prepare-train run-00X ─► test ─► đăng ký EXPERIMENTS.md ─► tag ─► [DUYỆT] push
   │        └──────────────────────────────────────────────────────────────┬──────────────┘
   │                                                                       ▼
   │                                                          GitHub (code + tag)
   │                                                                       │ clone/pull tag
   │                                                                       ▼
   │                                              [NGƯỜI] chạy notebook Colab/Kaggle (GPU)
   │                                              tự lưu ckpt · ngắt phiên → Run all → resume
   │                                              lỗi → /fix-remote-error
   │                                                                       │
   │                                          tải metrics.csv + summary.json về results/<run>/
   │                                                                       ▼
   └──────────────── experiment-analyst ◄──── /analyze-runs ◄──────────────┘
                     (cập nhật EXPERIMENTS.md, thêm ý tưởng vào IDEAS.md)
```

## 2. Các lớp giữ "quy củ"

| Lớp | Cơ chế | Ví dụ trong project |
|---|---|---|
| Kế hoạch trước khi làm | `planner` (chỉ đọc) trả về kế hoạch có **tiêu chí hoàn thành** | Mục "Ảnh hưởng checkpoint" buộc phải xét resume |
| Tự kiểm chứng | Test và smoke chạy trên CPU trong vài giây | `test_resume_gives_same_weights_as_uninterrupted` |
| Vòng debug có giới hạn | Tối đa 3 vòng, quá thì dừng và báo cáo | `/dev-cycle` bước 4 |
| Review độc lập | `code-reviewer` context sạch, chỉ báo lỗi đúng/sai và vi phạm quy tắc | BLOCKER thì quay lại test |
| Luật cứng | Hook + permission | Chặn force push, commit checkpoint; `git push` luôn hỏi |
| Điểm dừng cho người | Ghi rõ trong skill | Duyệt plan lớn, push, chọn ý tưởng, chạy GPU |
| Trạng thái trên đĩa | `PROGRESS.md`, `EXPERIMENTS.md`, `IDEAS.md`, git | Phiên mới đọc lại được, không phụ thuộc trí nhớ hội thoại |

> Bài học thật từ lúc dựng project: phiên bản đầu của `src/data.py` resume **gần đúng** nhưng không giống hệt,
> vì mỗi lần tạo DataLoader lại rút seed từ RNG toàn cục. Chỉ test so sánh trọng số "ngắt rồi resume" với
> "chạy một mạch" mới bắt được lỗi này. Test tốt là thứ cho phép Claude tự làm mà bạn vẫn yên tâm.

## 3. Ví dụ trọn vòng

### A. Ý tưởng chỉ đổi config: label smoothing
```
> /idea-loop
```
1. Claude đọc `IDEAS.md` và bảng kết quả (chèn sẵn nhờ `` !`...` ``). Baseline chưa chạy thì baseline được chọn trước.
2. Giả sử baseline đã có kết quả. Claude đề xuất ý tưởng #2 (label smoothing, config-only, rẻ) và hỏi bạn một câu.
3. Bạn đồng ý. Claude gọi `/new-experiment ls01 train.label_smoothing=0.1`: tạo `configs/exp_ls01.yaml`, chạy smoke, commit.
4. Claude dừng và gợi ý: `/prepare-train run-002-ls01 configs/exp_ls01.yaml`.
5. Bạn chạy lệnh đó. Claude test, đăng ký run, tạo tag, rồi **hỏi quyền push**. Bạn duyệt.
6. Bạn mở notebook, sửa `REF`/`RUN_NAME`/`CONFIG` theo khối Claude in ra, rồi Run all.
7. Xong run, bạn chép `metrics.csv` và `summary.json` về `results/run-002-ls01/` rồi gõ `/analyze-runs`.

### B. Ý tưởng cần sửa code: Mixup
```
> /dev-cycle Thêm Mixup vào vòng train: train.mixup_alpha trong config, mặc định 0 (tắt), có test
```
Những gì bạn sẽ thấy:
1. `planner` trả về kế hoạch: sửa `src/train.py` (trộn batch, loss hai nhãn), thêm key vào `configs/base.yaml`, thêm test.
   Mục *Ảnh hưởng checkpoint*: không (key mới có mặc định). Claude tóm tắt rồi tiếp tục.
2. `implementer` code và tự chạy smoke.
3. `test-runner` (Haiku) báo `KẾT QUẢ: PASS | FAIL`.
4. FAIL thì `debugger` nhận nguyên văn lỗi, viết test tái hiện, sửa, rồi quay lại bước 3.
5. `code-reviewer` kiểm tra: RNG của Mixup có làm resume lệch không? Có test chưa?
6. Commit `feat: mixup`, cập nhật `PROGRESS.md`, rồi báo cáo kèm bằng chứng test.

### C. Lỗi trên Colab
```
> /fix-remote-error run-002-ls01
  (dán traceback)
```
`debugger` phân loại lỗi. Lỗi môi trường (thiếu Internet, OOM, sai secret) thì Claude chỉ cách thao tác.
Lỗi code thì Claude sửa, test, commit, và hướng dẫn tạo tag `run-002-ls01b`, đổi `REF`, **giữ nguyên `RUN_NAME`** để resume.

## 4. Chạy lâu hơn mà ít phải trông

| Công cụ | Dùng khi | Ví dụ |
|---|---|---|
| **Auto mode** | Bớt hỏi quyền từng tool; model phân loại chặn hành động rủi ro | `Shift+Tab` tới `⏵⏵ auto mode on` |
| **`/goal`** | Làm tiếp nhiều lượt tới khi điều kiện kiểm chứng được thì đạt | `/goal pytest -q pass hết và smoke train chạy xong với configs/exp_mixup.yaml, dừng sau 15 lượt` |
| **Stop hook** | Cổng chặn tất định cho mọi phiên | Ví dụ `require_tests.py` ở [04](04-harness.md) |
| **Headless `claude -p`** | Chạy từ script hoặc CI, không mở giao diện | xem dưới |
| **`/loop`** | Lặp theo chu kỳ khi phiên còn mở | `/loop 30m kiểm tra results/ có run mới thì /analyze-runs` |

`/goal` hoạt động thế nào: sau mỗi lượt, một model nhỏ (mặc định Haiku) đọc hội thoại và đánh giá điều kiện.
Chưa đạt thì Claude làm tiếp. Viết điều kiện là **thứ Claude chứng minh được bằng output** (lệnh test exit 0),
kèm giới hạn ("dừng sau 15 lượt"). `/goal` không đổi permission mode; muốn chạy không cần trông thì kết hợp auto mode.

Headless:
```bash
# Skill do người gọi vẫn dùng được trong -p: đưa /tên-skill vào prompt
claude -p "/dev-cycle Thêm tùy chọn optimizer adamw vào test" --permission-mode auto --output-format json
```
- Ở `-p`, không có ai trả lời câu hỏi quyền. Lệnh thuộc quy tắc `ask` (như `git push`) sẽ bị từ chối. Đây là hàng rào tốt.
- `--permission-prompts none` (từ v2.1.259) báo trước cho Claude rằng không ai duyệt được, để nó không thử lại.
- `--output-format json` trả về `result`, `session_id`, chi phí. Làm tiếp bằng `claude -p "..." --resume <session_id>`.
- Nếu thư mục **chưa được trust**, `-p` in `Ignoring N permissions.allow entries ... workspace has not been trusted` và bỏ qua
  các quy tắc allow của project, **nhưng hooks vẫn chạy**. Mở `claude` tương tác một lần trong thư mục và chấp nhận
  hộp thoại trust là xong.

Chạy song song: dùng `/branch`, git worktree, hoặc `claude agents` (xem docs "Worktrees", "Agent view") để một phiên làm Mixup,
một phiên làm tài liệu, không đụng file của nhau.

## 5. Khi nào con người phải vào cuộc

| Tín hiệu | Việc của bạn |
|---|---|
| Planner ghi "cần RUN_NAME mới" | Quyết định có đáng train lại từ đầu không |
| `/dev-cycle` dừng sau 3 vòng debug | Đọc báo cáo, cung cấp thêm thông tin hoặc thu hẹp task |
| Claude hỏi quyền `git push` | Kiểm tra `git log origin/main..HEAD` rồi duyệt |
| Kết quả chênh lệch trong nhiễu (dưới khoảng 0.3%) | Quyết định chạy lại seed khác hay bỏ ý tưởng |
| Hook chặn một hành động | Đọc lý do. Nếu hook sai, sửa hook (Claude sẽ phải xin quyền vì `protect_files` đặt `ask`) |

## 6. Mở rộng quy trình cho project của bạn
1. Bắt đầu bằng **test chạy nhanh trên CPU**. Không có nó thì không tự động hóa được gì an toàn.
2. Viết `CLAUDE.md` ngắn: lệnh và quy tắc.
3. Thêm hook cho 2–3 quy tắc bạn không bao giờ muốn bị vi phạm.
4. Tách vai trò thành subagent khi thấy context chính bị đầy vì đọc file, hoặc khi cần review độc lập.
5. Đóng gói chuỗi việc lặp lại thành skill; ghi rõ điểm dừng cho người.
6. Đo và chỉnh: xem `/usage`, rồi hạ model/effort cho vai trò máy móc (test-runner) và giữ model mạnh cho vai trò suy luận (planner, debugger).
