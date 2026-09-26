# 00 · Lộ trình học Claude Code qua project này

Project này là một bài toán ML nhỏ: train CNN phân loại CIFAR-10. Máy cá nhân không có GPU, nên code được viết local,
đẩy lên GitHub, rồi train trên Colab/Kaggle. Bài toán cố ý đơn giản để người học tập trung vào **cách làm việc với
Claude Code**, gồm cài đặt, chọn model, quản lý context, harness (settings/hooks), subagent, skill, và một quy trình
tự động có kiểm soát.

## Bản đồ: khái niệm → file để xem trong repo

| Khái niệm | Xem ở đâu | Tài liệu |
|---|---|---|
| Chỉ dẫn dự án cho Claude (memory) | `CLAUDE.md`, `.claude/rules/training-code.md` | [04](04-harness.md) |
| Quyền (allow / ask / deny) | `.claude/settings.json` → `permissions` | [04](04-harness.md) |
| Hooks (kiểm tra bắt buộc) | `.claude/settings.json` → `hooks`, `.claude/hooks/*.py` | [04](04-harness.md) |
| Subagent (phân vai) | `.claude/agents/*.md` | [05](05-agents-va-skills.md) |
| Skill / lệnh `/...` tự định nghĩa | `.claude/skills/*/SKILL.md` | [05](05-agents-va-skills.md) |
| Quy trình tự động | `/dev-cycle`, `/idea-loop`, `IDEAS.md` | [06](06-quy-trinh-tu-dong.md) |
| Chạy trên Colab/Kaggle, resume | `src/train.py`, `notebooks/`, `scripts/make_notebooks.py` | [07](07-colab-kaggle.md) |
| "Cho Claude cách tự kiểm chứng" | `tests/test_train.py` | [06](06-quy-trinh-tu-dong.md) |
| Theo dõi run từ xa: Colab đẩy log lên git | `src/utils/run_logger.py`, `scripts/sync_runs.py`, `/run-status` | [08](08-demo-colab-git-log.md) |
| Kết nối trực tiếp: Claude chạy cell trên Colab | `notebooks/vscode_colab.ipynb`, tool `mcp__ide__executeCode` | [09](09-vscode-colab.md) |

## Kế hoạch 5 buổi (mỗi buổi khoảng 90 phút)

### Buổi 1: Cài đặt và làm quen ([01](01-cai-dat.md), [03](03-lenh-va-co-che.md))
- Cài Claude Code, đăng nhập, mở project, chạy `/context` để thấy `CLAUDE.md` đã được nạp.
- Hỏi Claude về codebase: *"Giải thích cơ chế resume trong src/train.py"*.
- Thực hành `Esc` (ngắt), `Esc Esc` / `/rewind` (quay lại), `/clear`, `/resume`, `!git status`, `@src/model.py`.
- **Bài tập:** nhờ Claude đổi dòng log trong `src/train.py`, rồi dùng `/rewind` → *Restore code* để hoàn tác.

### Buổi 2: Model, effort và chế độ quyền ([02](02-models-va-modes.md))
- So sánh `/model sonnet` và `/model opus` trên cùng câu hỏi; thử `/effort low` và `/effort high`.
- `Shift+Tab` qua các chế độ Manual → acceptEdits → plan (→ auto).
- Plan mode: *"Lên kế hoạch thêm Mixup"*, sửa plan bằng `Ctrl+G`, duyệt plan rồi để Claude code.
- **Bài tập:** đo `/usage` sau cùng một task với Haiku và với Opus, rồi rút ra khi nào dùng model nào.

### Buổi 3: Harness ([04](04-harness.md))
- Đọc `.claude/settings.json`. Thử yêu cầu Claude `git push --force` và xem hook chặn ra sao.
- Test hook bằng tay: `echo '{...}' | python .claude/hooks/guard_bash.py`.
- Sửa cố ý một file `.py` cho sai cú pháp, xem hook `check_python` báo lại cho Claude.
- **Bài tập:** viết thêm một hook `Notification` phát tiếng bíp khi Claude cần bạn duyệt quyền.

### Buổi 4: Subagent và skill ([05](05-agents-va-skills.md))
- *"Dùng subagent test-runner chạy test"* và `@agent-code-reviewer review thay đổi hiện tại`.
- Chạy `/new-experiment ls01 train.label_smoothing=0.1`, rồi đọc file config được tạo ra.
- **Bài tập:** nhờ Claude tạo subagent mới `doc-writer` (chỉ sửa `docs/`, model haiku) và dùng thử.

### Buổi 5: Quy trình tự động end-to-end ([06](06-quy-trinh-tu-dong.md), [07](07-colab-kaggle.md))
- Demo [08](08-demo-colab-git-log.md): `/prepare-train run-001-demo` → Colab chạy với `LOG_BRANCH="runs"` → hỏi Claude
  *"run đang tới đâu?"* → cố ý ngắt, rồi crash → Claude đọc log từ branch `runs` mà không cần bạn dán gì.
- Tải kết quả về `results/`, chạy `/analyze-runs`, rồi `/idea-loop` để chọn và hiện thực ý tưởng tiếp theo.
- **Bài tập:** `/dev-cycle Thêm Mixup vào vòng train (alpha trong config, mặc định tắt)` và quan sát đủ 6 bước.

## Nguyên tắc xuyên suốt
1. **Cho Claude cách tự kiểm chứng**: có test và smoke thì Claude tự lặp tới khi đúng, không cần bạn soi từng dòng.
2. **Context là tài nguyên quý nhất**: dùng `/clear` giữa các task, giao việc đọc nhiều file cho subagent.
3. **CLAUDE.md chỉ là lời khuyên, hook mới là luật**: việc *bắt buộc* thì viết thành hook hoặc quy tắc permission.
4. **Con người giữ các quyết định đầu ra**: push, dùng GPU và chọn hướng thí nghiệm là việc của người.
