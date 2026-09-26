# 05 · Subagent và Skill: xây "đội" cho Claude

## 1. Chọn công cụ nào?

| Công cụ | Bản chất | Context | Ai kích hoạt | Dùng cho |
|---|---|---|---|---|
| **CLAUDE.md / rules** | Chỉ dẫn luôn có mặt | Context chính, mọi lúc | Tự động | Quy ước áp dụng mọi lúc |
| **Skill** | Gói chỉ dẫn/quy trình, nạp **khi cần** | Context chính (hoặc fork sang subagent) | Claude tự chọn theo `description`, hoặc bạn gõ `/tên` | Quy trình lặp lại, kiến thức chuyên đề |
| **Subagent** | "Nhân viên" có system prompt, tool, model riêng | **Context riêng**, chỉ trả về tóm tắt | Claude giao việc theo `description`, hoặc bạn chỉ định | Việc đọc nhiều, cần góc nhìn độc lập, cần giới hạn quyền |
| **Hook** | Script tất định | Không dùng context (trừ khi in ra) | Sự kiện | Việc *bắt buộc* ([04](04-harness.md)) |

Hai câu hỏi để chọn:
- *"Việc này có làm đầy context chính không?"* Có thì dùng **subagent**.
- *"Đây là quy trình tôi gõ đi gõ lại?"* Có thì dùng **skill**.

## 2. Subagent

### Cơ chế
- Subagent chạy trong **context riêng**. Nó nhận system prompt của mình, lời giao việc từ Claude, các file CLAUDE.md,
  git status và skill được nạp sẵn. Nó **không thấy** lịch sử hội thoại chính.
  → Khi giao việc phải đưa đủ bối cảnh. CLAUDE.md của project nhắc điều này.
- Làm xong, nó trả về một bản tóm tắt. Context chính chỉ tăng thêm bản tóm tắt đó, không phải hàng chục file nó đã đọc.
- Subagent có thể gọi subagent khác, sâu tối đa 3 tầng (mặc định). Chạy song song tối đa 20.
- Thay đổi file do subagent tạo ra **không** hoàn tác được bằng `/rewind`, nên hãy dùng git ([03](03-lenh-va-co-che.md)).

### Subagent có sẵn
- **Explore**: chỉ đọc, tìm kiếm codebase nhanh (mức quick / medium / very thorough).
- **Plan**: chỉ đọc, nghiên cứu phục vụ plan mode.
- **general-purpose**: mọi tool, cho việc nhiều bước.

### Cấu trúc file (`.claude/agents/<tên>.md`)
```markdown
---
name: test-runner                    # bắt buộc, định danh duy nhất
description: Chạy pytest và smoke test ... Dùng proactively sau mỗi lần sửa code.   # bắt buộc
tools: Bash, Read                    # allowlist tool (bỏ trống = kế thừa mọi tool)
model: haiku                         # sonnet | opus | haiku | fable | inherit | model id đầy đủ
effort: low                          # low | medium | high | xhigh | max
color: yellow
---
(Phần thân là system prompt của subagent: vai trò, quy trình, mẫu báo cáo.)
```
Các trường khác hay dùng: `disallowedTools` (denylist), `permissionMode`, `maxTurns`, `skills` (nạp sẵn skill),
`memory: project|user|local` (bộ nhớ riêng qua các phiên), `isolation: worktree` (làm việc trong git worktree riêng),
`background: true`, `hooks` (hook riêng khi agent chạy), `mcpServers`.

### Claude chọn subagent thế nào
- Claude đọc `description` của mọi agent. Viết description rõ **khi nào dùng**; thêm "Dùng proactively ..." để Claude tự giao việc.
- Gọi chỉ định bằng lời: *"Dùng subagent code-reviewer review thay đổi"*.
- Bắt buộc gọi bằng @-mention: `@agent-code-reviewer xem thay đổi hiện tại`.
- Cả phiên chạy như một agent: `claude --agent experiment-analyst`.

### Đội của project này

```
                      ┌──────────────┐
      người dùng ───► │ phiên chính  │  (điều phối, thường là Opus)
                      └──────┬───────┘
     ┌─────────────┬─────────┼──────────┬──────────────┬────────────────────┐
     ▼             ▼         ▼          ▼              ▼                    ▼
  planner     implementer  test-runner  debugger   code-reviewer   experiment-analyst
  opus·high   sonnet       haiku·low    opus       sonnet          sonnet·memory
  chỉ đọc     sửa code     chỉ chạy     sửa lỗi    chỉ đọc         sửa EXPERIMENTS/IDEAS
```

| Agent | Tool | Vì sao thiết kế vậy |
|---|---|---|
| `planner` | Read, Grep, Glob, Web | Không có Edit, nên lập kế hoạch mà không "tiện tay" sửa code. Opus/high cho suy luận tốt |
| `implementer` | Đủ tool sửa code | Sonnet đủ giỏi khi đã có kế hoạch chi tiết, rẻ hơn Opus |
| `test-runner` | Bash, Read | Haiku/low: việc máy móc, cần nhanh và rẻ. Báo cáo theo mẫu cố định để phiên chính dễ đọc |
| `debugger` | Đủ tool | Opus: debug cần suy luận. Quy trình bắt phân loại lỗi môi trường / resume / code trước khi sửa |
| `code-reviewer` | Read, Grep, Glob, Bash | Context sạch: không thấy quá trình viết nên không thiên vị code vừa viết |
| `experiment-analyst` | Đọc, chạy script, sửa `.md` | `memory: project` nhớ bài học qua các lần phân tích (`.claude/agent-memory/experiment-analyst/`) |

### Tạo subagent mới
Từ v2.1.198, `/agents` không còn wizard. Cách làm là nhờ Claude viết:
> *"Tạo subagent `doc-writer` trong .claude/agents/: chỉ sửa file trong docs/, model haiku, dùng khi cần cập nhật tài liệu
> sau khi code thay đổi. Mẫu báo cáo: danh sách file đã sửa."*

Hoặc tự tạo file. Claude Code nhận file mới trong vài giây, không cần khởi động lại.

## 3. Skill

### Cơ chế
- Lúc khởi động, chỉ **mô tả** (`description`) của mỗi skill nằm trong context, nên rất rẻ.
  Toàn bộ nội dung chỉ nạp khi skill được dùng.
- Skill có `disable-model-invocation: true` không có cả mô tả trong context. Nó tốn 0 token cho tới khi bạn gõ `/tên`.
- Skill thay thế "custom slash command" cũ: `.claude/commands/x.md` vẫn chạy, nhưng nên dùng `.claude/skills/x/SKILL.md`
  (hỗ trợ file đi kèm và nhiều frontmatter hơn).

### Cấu trúc (`.claude/skills/<tên>/SKILL.md`)
```markdown
---
name: prepare-train
description: Chuẩn bị một run train trên Colab/Kaggle ...     # Claude dùng để quyết định tự gọi
argument-hint: "<run-name> [config]"                          # gợi ý khi gõ /
arguments: [run, config]                                      # tham số có tên → $run, $config
disable-model-invocation: true                                # chỉ người gọi được (có tác dụng phụ: push)
allowed-tools: Bash(git tag *) Bash(git status *)             # tự duyệt các tool này trong lượt skill chạy
---
**Run:** `$run`. **Config:** `$config`

## Trạng thái hiện tại
!`git status --short || true`          ← chạy lệnh TRƯỚC khi gửi cho Claude, output thay vào chỗ này
...
```

| Cú pháp | Ý nghĩa |
|---|---|
| `$ARGUMENTS` | Toàn bộ tham số sau `/tên` |
| `$0`, `$1` / `$tên` | Tham số theo vị trí / theo tên khai báo trong `arguments` |
| `` !`lệnh` `` | Chèn output của lệnh shell vào skill trước khi Claude đọc (lệnh lỗi thì hủy skill, nên thêm `\|\| true`) |
| `${CLAUDE_SKILL_DIR}` | Thư mục chứa SKILL.md (để gọi script đi kèm) |

| Frontmatter | Ý nghĩa |
|---|---|
| `disable-model-invocation: true` | Chỉ bạn gọi được. Dùng cho việc có tác dụng phụ (commit, push, deploy) |
| `user-invocable: false` | Chỉ Claude gọi được (ẩn khỏi menu `/`). Dùng cho kiến thức nền |
| `context: fork` + `agent: <tên>` | Chạy skill **trong một subagent**; nội dung skill thành prompt của subagent |
| `background: false` | (với fork) chờ kết quả ngay trong lượt hiện tại |
| `model`, `effort` | Ghi đè model/effort khi skill chạy |
| `paths` | Chỉ tự nạp khi làm việc với file khớp mẫu |

### Các skill của project

| Skill | Gọi bởi | Minh họa |
|---|---|---|
| `/dev-cycle <task>` | Người | Điều phối cả đội subagent theo quy trình cố định; `` !`git status` `` chèn trạng thái repo |
| `/prepare-train <run> [config]` | Người | Tham số có tên, `allowed-tools`, dừng ở `git push` để người duyệt (quy tắc `ask`) |
| `/fix-remote-error` | Người | Quy trình xử lý lỗi từ Colab/Kaggle |
| `/analyze-runs` | Người **hoặc Claude** | `context: fork` + `agent: experiment-analyst`: skill chạy trong subagent |
| `/new-experiment <tên> <k=v...>` | Người hoặc Claude | Skill mà skill khác (`/idea-loop`) gọi được |
| `/idea-loop [auto]` | Người | Skill điều phối skill khác; chèn `IDEAS.md` và bảng kết quả |
| `colab-kaggle-runbook` | **Claude tự nạp** | Kiến thức chuyên đề: hỏi về Colab/Kaggle thì Claude tự đọc |

Vì sao `dev-cycle` đặt `disable-model-invocation: true`? Vì nó commit. Việc có tác dụng phụ nên để người chủ động gọi.
Hệ quả là `/idea-loop` không gọi được nó qua Skill tool, nên `/idea-loop` được viết là *"đọc `.claude/skills/dev-cycle/SKILL.md`
và làm theo"*.

### Viết skill tốt
- `description` nói rõ **làm gì và khi nào dùng**, vì Claude chọn skill dựa vào đó.
- Đặt chỉ dẫn quan trọng ở **đầu** file: sau compact, skill dài bị cắt còn khoảng 5.000 token đầu.
- Mỗi bước kết thúc bằng một điều kiện kiểm chứng được ("test-runner phải PASS").
- Nêu rõ chỗ **dừng để người quyết định** (duyệt plan, push, chọn ý tưởng).
