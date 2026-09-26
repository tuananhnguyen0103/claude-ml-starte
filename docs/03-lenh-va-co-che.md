# 03 · Lệnh và cơ chế bên dưới

Muốn dùng lệnh đúng lúc, cần hiểu 3 cơ chế: **context window**, **checkpoint** và **session**.

## 1. Ba cơ chế cần hiểu

### Context window: "bộ nhớ làm việc" của một phiên
Mọi thứ Claude "biết" trong phiên đều nằm trong context. **Trước khi bạn gõ gì**, context đã có:
system prompt, các file `CLAUDE.md`, auto memory (200 dòng đầu hoặc 25KB đầu của `MEMORY.md`), thông tin môi trường và git,
mô tả một dòng của mỗi skill, tên các tool MCP, và output của hook `SessionStart`.
Sau đó mỗi tin nhắn, mỗi file Claude đọc, mỗi output lệnh đều cộng dồn vào.

Context càng đầy, chất lượng càng giảm: Claude dễ "quên" chỉ dẫn đầu phiên. Khi gần đầy, Claude Code **tự động compact**,
tức thay hội thoại bằng một bản tóm tắt có cấu trúc.

**Còn lại gì sau khi compact:**

| Thành phần | Sau compact |
|---|---|
| `CLAUDE.md` ở gốc project, rule không có `paths` | Nạp lại từ đĩa |
| Auto memory | Nạp lại từ đĩa |
| Plan viết trong plan mode | Nạp lại từ đĩa |
| File đã đọc/sửa | Đọc lại **tối đa 5 file**, ưu tiên file sửa gần nhất |
| Nội dung skill đã gọi | Nạp lại, tối đa 5.000 token mỗi skill và 25.000 token tổng |
| Hook `SessionStart` có matcher `compact` | Chạy lại, output được thêm vào |
| Danh sách mô tả skill | **Không** nạp lại (chỉ skill đã gọi mới được giữ) |
| Output lệnh, suy luận trung gian | **Mất**, chỉ còn trong bản tóm tắt |

Vì vậy `CLAUDE.md` của project có mục "Khi compact", và hook `session_context.py` đăng ký cả matcher `compact`.

### Checkpoint: "undo" theo từng lượt
- Mỗi prompt bạn gửi (bắt đầu một lượt mới) tạo một checkpoint. Claude Code chụp lại file **trước khi** công cụ sửa file của Claude ghi đè.
- Giữ 100 checkpoint gần nhất mỗi phiên, lưu cùng hội thoại (resume xong vẫn rewind được). Snapshot bị dọn sau khoảng 30 ngày.
- **Không theo dõi được:** thay đổi do lệnh Bash (`rm`, `mv`, `sed -i`...), thay đổi ngoài Claude Code,
  và **phần lớn thay đổi do subagent** (trừ skill `context: fork` chạy foreground).
  → Đó là lý do quy trình `/dev-cycle` (subagent `implementer` sửa code) dựa vào **git** để quay lui, không dựa vào rewind.
- Checkpoint **không thay thế git**. Nó dùng cho hoàn tác nhanh trong phiên.

### Session: hội thoại được lưu trên đĩa
- Mỗi phiên là một file `~/.claude/projects/<project>/<session-id>.jsonl`, được ghi liên tục và giữ 30 ngày (đổi bằng `cleanupPeriodDays`).
- Đóng terminal, `/clear` hay hết hạn mức sử dụng đều không làm mất phiên. Có thể resume lại sau.

## 2. Bảng lệnh theo nhóm

### Quản lý context và phiên
| Lệnh | Cơ chế | Khi nào dùng |
|---|---|---|
| `/clear [tên]` | Bắt đầu hội thoại mới với context rỗng. Phiên cũ được **lưu lại** (resume bằng `/resume`, hoặc mục "previous session" trong menu rewind). Cũng xóa `/goal` đang chạy | Chuyển sang task không liên quan; sau 2 lần sửa sai mà Claude vẫn lệch |
| `/compact [chỉ dẫn]` | Tóm tắt hội thoại để giải phóng context. Chỉ dẫn quyết định giữ gì: `/compact giữ danh sách file đã sửa và lỗi resume` | Đang giữa task dài, context gần đầy |
| `/context [all]` | Hiển thị phần nào chiếm context | Kiểm tra CLAUDE.md đã nạp chưa, vì sao context đầy |
| `/rewind` hoặc `Esc Esc` | Mở menu checkpoint (xem mục 3) | Claude đi sai hướng, muốn quay lại |
| `/resume [tên]` | Chuyển sang phiên cũ | Quay lại việc hôm qua |
| `/branch [tên]` | Sao chép hội thoại hiện tại thành nhánh mới, bản gốc giữ nguyên | Thử hướng khác mà không mất hướng cũ |
| `/rename <tên>` | Đặt tên phiên để resume bằng tên | Mỗi luồng việc một tên: `mixup`, `fix-resume` |
| `/export [file]` | Xuất hội thoại ra text | Lưu lại để chia sẻ hay review |
| `/btw <câu hỏi>` | Hỏi bên lề, câu trả lời **không** vào lịch sử | Hỏi nhanh mà không làm đầy context |
| `/autocompact 500k` | Đặt ngưỡng tự compact | Muốn compact sớm hơn |

### Model và hiệu năng ([02](02-models-va-modes.md))
`/model [tên]`, `/effort [mức]`, `/fast [on|off]`, `/advisor [model|off]` (tool "cố vấn": hỏi model mạnh hơn khi gặp quyết định khó).

### Dự án, cấu hình, mở rộng ([04](04-harness.md), [05](05-agents-va-skills.md))
| Lệnh | Tác dụng |
|---|---|
| `/init` | Sinh `CLAUDE.md` khởi đầu từ code |
| `/memory` | Mở và sửa các file CLAUDE.md, bật/tắt auto memory |
| `/plan [mô tả]` | Vào plan mode cho prompt này |
| `/permissions` | Xem và sửa quy tắc allow/ask/deny |
| `/config [key=value]` | Mở giao diện settings hoặc đặt giá trị trực tiếp |
| `/hooks` | Xem các hook đang cấu hình |
| `/mcp` | Quản lý MCP server (trạng thái, OAuth, bật/tắt) |
| `/agents` | Nhắc bạn tạo/sửa subagent bằng cách nhờ Claude hoặc sửa `.claude/agents/` (từ v2.1.198 không còn wizard) |
| `/add-dir <path>` | Cho phép truy cập thêm thư mục trong phiên |

### Tự động hóa và review
| Lệnh | Tác dụng |
|---|---|
| `/goal <điều kiện>` | Claude làm tiếp nhiều lượt tới khi một model đánh giá điều kiện đã đạt. `/goal clear` để hủy ([06](06-quy-trinh-tu-dong.md)) |
| `/loop [khoảng] <prompt>` | Chạy lại prompt theo chu kỳ khi phiên còn mở |
| `/tasks` | Xem việc nền (subagent, lệnh nền) |
| `/background [prompt]` | Đưa phiên hiện tại chạy nền |
| `/code-review` (alias `/review`) | Subagent review diff tìm lỗi, có các mức `low`…`max` |
| `/security-review` | Kiểm tra lỗ hổng bảo mật trong diff |
| `/diff` | Xem thay đổi trong working tree |

### Thông tin và tài khoản
`/status` (model, tài khoản), `/usage` (token và chi phí), `/help`, `/doctor` (chẩn đoán cài đặt), `/debug` (bật log debug),
`/login`, `/logout`, `/exit`.

### Lệnh của project này (skill trong `.claude/skills/`)
`/dev-cycle`, `/prepare-train`, `/fix-remote-error`, `/analyze-runs`, `/new-experiment`, `/idea-loop`,
cùng `colab-kaggle-runbook` (Claude tự nạp khi bạn hỏi về Colab/Kaggle). Chi tiết ở [05](05-agents-va-skills.md) và [06](06-quy-trinh-tu-dong.md).

## 3. `/rewind` chi tiết
Nhấn `Esc` hai lần khi ô nhập trống, hoặc gõ `/rewind`. Chọn một tin nhắn cũ, rồi chọn hành động:

| Lựa chọn | Code | Hội thoại |
|---|---|---|
| **Restore code and conversation** | Về như lúc đó | Về như lúc đó |
| **Restore conversation** | Giữ nguyên hiện tại | Về như lúc đó |
| **Restore code** | Về như lúc đó | Giữ nguyên |
| **Summarize from here** | Không đổi | Nén phần **từ đây trở đi** thành tóm tắt |
| **Summarize up to here** | Không đổi | Nén phần **trước đây**, giữ nguyên phần sau |
| Never mind | – | – |

- Hai lựa chọn Restore code chỉ hiện khi checkpoint đó có thay đổi file được theo dõi.
- Summarize giống một `/compact` có chọn phạm vi. Có thể gõ chỉ dẫn vào dòng "add context (optional)".
- Muốn giữ cả hai hướng thì dùng `/branch`, không dùng rewind.

## 4. Phím tắt và tiền tố nhập

| Phím / tiền tố | Tác dụng |
|---|---|
| `Esc` | Ngắt Claude đang làm (context vẫn còn, có thể nói lại hướng khác) |
| `Esc Esc` | Ô nhập có chữ thì xóa chữ; ô trống thì mở menu rewind |
| `Shift+Tab` (Windows có thể là `Alt+M`) | Đổi permission mode |
| `Alt+T` | Đổi effort cho phiên hiện tại |
| `Ctrl+O` | Bật/tắt xem transcript chi tiết (thấy tool call, output) |
| `Ctrl+R` | Tìm trong lịch sử lệnh đã gõ |
| `Ctrl+B` | Đưa tác vụ đang chạy xuống nền |
| `Ctrl+T` | Hiện/ẩn checklist công việc của Claude |
| `Ctrl+G` | Mở prompt (hoặc plan) trong editor |
| `Ctrl+S` | Cất tạm prompt đang gõ / lấy lại |
| `Alt+V` (Windows) | Dán ảnh từ clipboard |
| `Ctrl+C` / `Ctrl+D` | Ngắt hoặc xóa ô nhập / thoát |
| `/` đầu dòng | Lệnh hoặc skill |
| `!` đầu dòng | Chạy lệnh shell trực tiếp, output vào hội thoại: `!git status` |
| `@` | Nhắc tới file (có autocomplete): `giải thích @src/data.py` |
| `Enter` khi Claude đang chạy | **Xếp hàng** tin nhắn, không ngắt. `Ctrl+Enter` để gửi ngay |

## 5. Chọn lệnh theo tình huống

| Tình huống | Làm gì |
|---|---|
| Xong task A, chuyển sang task B không liên quan | `/clear` |
| Đang giữa task dài, context gần đầy | `/compact <giữ gì>` |
| Claude vừa làm sai hướng | `Esc`, nói lại cho rõ |
| Đã sửa sai 2 lần mà vẫn lệch | `/rewind` về trước đó, hoặc `/clear` rồi viết prompt tốt hơn kèm điều vừa học được |
| Muốn thử cách khác mà giữ cách cũ | `/branch` |
| Hỏi nhanh một chi tiết | `/btw` |
| Task cần đọc rất nhiều file | *"Dùng subagent để tìm hiểu …"*: đọc trong context riêng |
| Hôm sau làm tiếp | `claude --continue` hoặc `claude --resume <tên>` |

## 6. Khi Claude Code hết hạn mức sử dụng hoặc context
Việc train trên Colab/Kaggle **không phụ thuộc** vào phiên Claude, nó vẫn chạy.

**Phòng ngừa:** chia task nhỏ, xong task nào commit task đó. Cuối mỗi task, Claude cập nhật `PROGRESS.md` (quy tắc 9 trong CLAUDE.md).

**Khi bị chặn giữa chừng:**
1. Code đã sửa vẫn nằm trên đĩa. Kiểm tra bằng `git status` và `git diff`.
2. Cất phần dở vào nhánh riêng: `git switch -c wip/<task> && git add -A && git commit -m "wip: <đang làm gì>"`.
3. Ghi 2–3 dòng vào `PROGRESS.md`.
4. Khi có hạn mức trở lại:
   - `claude --continue` (phiên gần nhất) hoặc `claude --resume <tên>`.
   - Hoặc mở phiên mới. Hook `SessionStart` tự nạp branch, file đang sửa và trích `PROGRESS.md`, nên chỉ cần nói
     *"Tiếp tục task trong PROGRESS.md"*.
   - Trên gói Pro/Max, resume một phiên lớn (trên 100K token) bỏ dở hơn khoảng 1 giờ sẽ có hộp thoại chọn
     **Resume from summary** (rẻ hơn) hoặc **Resume full session as-is** (giữ đủ chi tiết).
