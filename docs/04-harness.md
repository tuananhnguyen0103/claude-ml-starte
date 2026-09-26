# 04 · Harness: "chèn" quy tắc và tự động hóa vào Claude Code

**Harness** là mọi thứ bao quanh model, quyết định model *thấy gì* và *được làm gì*. Claude Code cho bạn chèn vào
harness ở nhiều lớp. Điều cần nhớ nhất: các lớp khác nhau về **mức độ bắt buộc**.

| Lớp | File | Tính chất | Dùng cho |
|---|---|---|---|
| Memory | `CLAUDE.md`, `.claude/rules/*.md`, auto memory | **Lời khuyên**: Claude đọc như ngữ cảnh, *có thể* không theo | Lệnh build/test, quy ước, bẫy thường gặp |
| Permissions | `settings.json` → `permissions` | **Bắt buộc**: Claude Code chặn hoặc hỏi | Cho phép, hỏi hoặc cấm từng loại tool/lệnh |
| Hooks | `settings.json` → `hooks` + script | **Bắt buộc, tất định**: script luôn chạy | Kiểm tra bắt buộc, tự động hóa theo sự kiện |
| Skills | `.claude/skills/*/SKILL.md` | Nạp khi cần | Quy trình lặp lại, kiến thức chuyên đề ([05](05-agents-va-skills.md)) |
| Subagents | `.claude/agents/*.md` | Context riêng, tool riêng | Phân vai ([05](05-agents-va-skills.md)) |
| MCP | `.mcp.json` | Thêm tool bên ngoài | GitHub, DB, Notion... |

> Quy tắc ngón tay cái: nếu bạn đã nhắc Claude hai lần mà nó vẫn quên, và việc đó **bắt buộc** phải đúng,
> đừng viết thêm vào CLAUDE.md. Hãy biến nó thành **hook** hoặc **quy tắc deny**.

---

## 1. Memory: CLAUDE.md và rules

**Vị trí và thứ tự nạp** (tất cả được **ghép lại**, không ghi đè nhau):

| Phạm vi | File | Ai thấy |
|---|---|---|
| Tổ chức | managed CLAUDE.md (do admin triển khai) | Mọi người trong tổ chức |
| Cá nhân | `~/.claude/CLAUDE.md`, `~/.claude/rules/` | Bạn, mọi project |
| Project | `./CLAUDE.md` hoặc `./.claude/CLAUDE.md`, `.claude/rules/` | Cả nhóm (commit lên git) |
| Cá nhân trong project | `./CLAUDE.local.md` | Chỉ bạn (thêm vào `.gitignore`) |
| Thư mục con | `src/CLAUDE.md`... | Nạp khi Claude đọc file trong thư mục đó |

- Claude Code nạp CLAUDE.md từ thư mục hiện tại **và mọi thư mục cha**. File gần thư mục làm việc được đọc sau cùng.
- **Import:** trong CLAUDE.md viết `@docs/quy-uoc.md` để nhúng file khác (đường dẫn tương đối theo file chứa nó,
  tối đa 4 cấp lồng nhau). File import được nạp **ngay khi khởi động**, nên vẫn tốn context. Muốn Claude chỉ đọc khi cần
  thì ghi đường dẫn trong backtick (`` `docs/07-colab-kaggle.md` ``) như CLAUDE.md của project này.
- **Kích thước:** nên **dưới 200 dòng**. File càng dài, Claude càng dễ bỏ sót. Với mỗi dòng, hãy hỏi:
  *"Xóa dòng này thì Claude có làm sai không?"*
- **Rule theo đường dẫn:** file trong `.claude/rules/` có frontmatter `paths` chỉ nạp khi Claude đọc file khớp mẫu.
  Ví dụ trong project là `.claude/rules/training-code.md`, chỉ nạp khi làm việc với `src/**/*.py`, `tests/**/*.py`:
  ```markdown
  ---
  paths:
    - "src/**/*.py"
  ---
  # Quy tắc khi sửa code train
  - ...
  ```
- **Auto memory:** Claude tự ghi chú những gì học được (lệnh build, lỗi hay gặp, sở thích của bạn) vào
  `~/.claude/projects/<project>/memory/`. Bật/tắt và xem bằng `/memory`.

## 2. Settings: các tầng và thứ tự ưu tiên

| Ưu tiên | File | Phạm vi |
|---|---|---|
| 1 (cao nhất) | managed settings | Tổ chức (admin) |
| 2 | cờ dòng lệnh (`--settings`, `--model`...) | Phiên này |
| 3 | `.claude/settings.local.json` | Bạn, project này (không commit) |
| 4 | `.claude/settings.json` | Cả nhóm, project này (commit) |
| 5 | `~/.claude/settings.json` | Bạn, mọi project |

- Giá trị đơn (như `model`): tầng cao hơn thắng. **Danh sách permission được gộp** từ mọi tầng.
- Thêm `"$schema": "https://json.schemastore.org/claude-code-settings.json"` để VS Code gợi ý và kiểm tra lỗi.
- Biến môi trường cho phiên: khóa `"env": {"TEN_BIEN": "gia tri"}`.

## 3. Permissions: allow / ask / deny

Trích `.claude/settings.json` của project:
```json
"permissions": {
  "allow": ["Bash(git status *)", "Bash(git commit *)", "Bash(.venv/Scripts/python -m pytest *)", "..."],
  "ask":   ["Bash(git push *)"],
  "deny":  ["Bash(git push --force *)", "Bash(git push -f *)", "Read(./.env)", "Read(./.env.*)", "Read(**/kaggle.json)"]
}
```

- **Thứ tự đánh giá: deny → ask → allow.** Khớp đầu tiên theo thứ tự đó quyết định kết quả. Một allow cụ thể
  **không** mở được ngoại lệ trong deny. Deny ở bất kỳ tầng nào cũng thắng allow ở tầng khác.
- `ask` luôn hỏi, kể cả ở auto mode. Vì vậy `git push` (hành động ra bên ngoài) luôn cần người duyệt.
- **Cú pháp:**

| Quy tắc | Khớp |
|---|---|
| `Bash(npm run build)` | Đúng lệnh đó |
| `Bash(git diff *)` | Mọi lệnh bắt đầu bằng `git diff ` (khoảng trắng trước `*` là quan trọng: `Bash(git diff*)` còn khớp `git diff-index`) |
| `Read(./.env)` | File `.env` ở thư mục hiện tại |
| `Edit(src/**)` | File trong `src/` (với allow: chỉ `./src`; với deny/ask: thư mục tên `src` ở mọi độ sâu) |
| `WebFetch(domain:pytorch.org)` | Fetch tới domain đó |
| `mcp__github__create_issue` | Một tool MCP cụ thể |
| `Agent(Explore)` | Subagent built-in Explore |

- **Giới hạn của pattern:** `Bash(git push --force *)` không khớp `git push origin main --force` vì `--force` nằm cuối.
  Pattern chỉ so khớp tiền tố. Với logic tinh hơn, dùng **hook** (mục 4). Project này làm đúng như vậy: `guard_bash.py`
  bắt `--force`, `-f`, `+refspec` ở mọi vị trí.
- Sửa quyền trong phiên bằng `/permissions`. Chọn "Yes, and don't ask again" khi được hỏi thì Claude Code tự thêm quy tắc allow.

## 4. Hooks: script chạy tự động theo sự kiện

### Các sự kiện hay dùng
| Sự kiện | Khi nào | Chặn được? |
|---|---|---|
| `SessionStart` | Bắt đầu hoặc resume phiên, sau `/clear`, sau compact | Không; stdout dạng text được **thêm vào context** |
| `UserPromptSubmit` | Bạn gửi prompt, trước khi Claude xử lý | Có; stdout thêm vào context |
| `PreToolUse` | Trước khi một tool chạy | **Có** (allow / deny / ask) |
| `PermissionRequest` | Khi cần quyết định quyền | Có |
| `PostToolUse` | Sau khi tool chạy thành công | Không (tool đã chạy); gửi phản hồi cho Claude được |
| `Notification` | Claude Code gửi thông báo (chờ duyệt quyền, rảnh) | Không |
| `Stop` / `SubagentStop` | Claude hoặc subagent trả lời xong | **Có**: bắt Claude làm tiếp |
| `PreCompact` / `PostCompact` | Trước / sau compact | – |
| `SessionEnd` | Kết thúc phiên | – |

(Còn nhiều sự kiện khác: `SubagentStart`, `PostToolUseFailure`, `FileChanged`, `PreModelSwitch`… Xem `/hooks` hoặc docs.)

### Cấu hình
```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "Bash|PowerShell",
      "hooks": [
        { "type": "command", "command": "python \"${CLAUDE_PROJECT_DIR}/.claude/hooks/guard_bash.py\"", "timeout": 30 }
      ]
    }
  ]
}
```
- `matcher`: tên tool. `"Edit|Write"` là danh sách; ký tự đặc biệt biến nó thành regex (`mcp__github__.*`); `"*"` hoặc để trống khớp tất cả.
  Với `SessionStart`, matcher là nguồn: `startup|resume|clear|compact`.
- `${CLAUDE_PROJECT_DIR}` là thư mục gốc project, **luôn bọc trong ngoặc kép** vì đường dẫn có thể có khoảng trắng.
- Trên Windows, hook chạy bằng **Git Bash** (nếu có), nếu không thì PowerShell. Có thể ép bằng `"shell": "powershell"`.

### Giao thức vào/ra
- **Vào:** JSON qua stdin, gồm `session_id`, `cwd`, `hook_event_name`, `permission_mode`, và với tool thì thêm `tool_name`, `tool_input`.
- **Exit code:**
  - `0`: thành công; stdout được đọc như JSON (nếu hợp lệ).
  - `2`: **lỗi chặn**. Với sự kiện chặn được, hành động bị chặn và stderr được gửi cho Claude.
  - Khác: lỗi không chặn, hành động vẫn tiếp tục.
- **Ra (JSON)**, ví dụ chặn một lệnh ở `PreToolUse`:
  ```json
  {"hookSpecificOutput": {"hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Force push bị cấm trong project này"}}
  ```
  `permissionDecision` nhận `allow` / `deny` / `ask`. Claude đọc `permissionDecisionReason` và tự điều chỉnh cách làm.
- Hook **không vượt qua được** quy tắc deny/ask: deny vẫn chặn dù hook trả `allow`.

### 4 hook của project này

| File | Sự kiện · matcher | Làm gì | Minh họa khái niệm |
|---|---|---|---|
| `session_context.py` | SessionStart · `startup\|resume\|clear\|compact` | In branch, file chưa commit, 5 commit gần nhất, trích `PROGRESS.md` | Nạp context tự động; nối tiếp sau khi hết hạn mức |
| `guard_bash.py` | PreToolUse · `Bash\|PowerShell` | Chặn force push, `git add -f`, commit data/checkpoint/secret/file > 5MB, lệnh in secret | Quyết định `deny` kèm lý do |
| `protect_files.py` | PreToolUse · `Edit\|Write\|NotebookEdit` | Chặn sửa secret, `.git/`, checkpoint, notebook sinh tự động; **hỏi** khi Claude sửa `.claude/settings.json` hoặc `.claude/hooks/` | `deny` và `ask` |
| `check_python.py` | PostToolUse · `Edit\|Write` | Kiểm tra cú pháp file `.py` vừa sửa bằng Python của venv; lỗi thì báo lại cho Claude qua `additionalContext` | Phản hồi sau hành động |

**Test hook bằng tay** (Git Bash, từ thư mục gốc). Cách này nhanh hơn nhiều so với thử qua Claude:
```bash
echo '{"tool_name":"Bash","tool_input":{"command":"git push origin main --force"}}' | python .claude/hooks/guard_bash.py
echo '{"tool_name":"Write","tool_input":{"file_path":".env"}}'                   | python .claude/hooks/protect_files.py
echo '{"source":"startup"}'                                                      | python .claude/hooks/session_context.py
```
Có hai lệnh `deny`: lệnh đầu in JSON có `"permissionDecision": "deny"`, lệnh thứ hai chặn sửa `.env`.
Khi hook cho phép, nó không in gì. `tests/test_hooks.py` kiểm tra tự động các trường hợp này.

### Thêm hook của riêng bạn: hai ví dụ

**Bíp khi Claude cần bạn** (Windows, chỉ thêm vào `.claude/settings.local.json` vì đây là sở thích cá nhân):
```json
{ "hooks": { "Notification": [ { "matcher": "permission_prompt|idle_prompt",
  "hooks": [ { "type": "command", "shell": "powershell", "command": "[console]::beep(880,300)" } ] } ] } }
```

**Cổng chặn "chưa pass test thì chưa được dừng"** (Stop hook). Phải kiểm tra `stop_hook_active`, nếu không sẽ lặp vô hạn:
```python
# .claude/hooks/require_tests.py
import json, subprocess, sys
data = json.load(sys.stdin)
if data.get("stop_hook_active"):          # đã chặn một lần rồi, cho dừng để tránh lặp
    sys.exit(0)
r = subprocess.run([".venv/Scripts/python", "-m", "pytest", "-q"], capture_output=True, text=True)
if r.returncode != 0:
    print("Test đang fail, sửa trước khi kết thúc:\n" + r.stdout[-1500:], file=sys.stderr)
    sys.exit(2)                            # exit 2 ở Stop: Claude nhận stderr và làm tiếp
```
Cổng kiểu này hợp với phiên tự động dài. Với phiên tương tác, nó có thể gây phiền.

### An toàn
Hook chạy **bằng quyền của bạn**, với bất kỳ lệnh nào nó chứa. Trước khi tin một repo lạ, hãy đọc `.claude/settings.json`
và các script hook. Claude Code hỏi workspace trust lần đầu mở thư mục chính là vì lý do này.

## 5. MCP: thêm tool bên ngoài
```bash
claude mcp add --transport http notion https://mcp.notion.com/mcp        # server HTTP
claude mcp add --transport stdio mytool -- npx -y some-mcp-server         # server chạy local (sau "--" là lệnh)
claude mcp add --scope project ...                                        # ghi vào .mcp.json để cả nhóm dùng
```
- Scope: `local` (mặc định, chỉ bạn trong project này), `project` (`.mcp.json`, commit được), `user` (mọi project của bạn).
- `.mcp.json` hỗ trợ biến môi trường: `"Authorization": "Bearer ${API_KEY}"`. Đừng ghi thẳng token vào file.
- Server trong `.mcp.json` cần bạn duyệt lần đầu. Quản lý bằng `/mcp`.
- Với GitHub, CLI `gh` thường tiết kiệm context hơn MCP, và Claude dùng `gh` rất thạo.

## 6. Plugin
Plugin đóng gói skill, hook, subagent và MCP thành một gói cài đặt được (`/plugin` để duyệt marketplace).
Khi bộ `.claude/` của project này ổn định, có thể đóng thành plugin để dùng lại cho các project ML khác.
