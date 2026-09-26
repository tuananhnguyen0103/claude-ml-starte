# 01 · Cài đặt Claude Code và mở project

> Nguồn: tài liệu chính thức tại https://code.claude.com/docs (cập nhật 09/2026). Tính năng thay đổi nhanh,
> gặp khác biệt thì chạy `claude update` và xem lại docs.

## 1. Yêu cầu
- Tài khoản **Claude Pro, Max, Team, Enterprise** hoặc **Claude Console** (API key). Gói claude.ai miễn phí không có Claude Code.
- Windows 10 1809+, macOS 13+, hoặc Ubuntu 20.04+/Debian 10+; RAM từ 4 GB.
- **Windows:** nên cài [Git for Windows](https://git-scm.com/downloads/win). Có nó thì Claude dùng Git Bash làm shell,
  và các hook của project chạy qua Git Bash. Không có thì Claude dùng PowerShell.

## 2. Cài đặt

| Hệ điều hành | Lệnh |
|---|---|
| macOS / Linux / WSL | `curl -fsSL https://claude.ai/install.sh \| bash` |
| Windows PowerShell | `irm https://claude.ai/install.ps1 \| iex` |
| Windows CMD | `curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd` |
| Homebrew / WinGet | `brew install --cask claude-code` / `winget install Anthropic.ClaudeCode` |

Kiểm tra: mở terminal mới, chạy `claude --version`, sau đó `claude doctor` để chẩn đoán cài đặt và file settings.
Bản cài native tự cập nhật. Muốn cập nhật ngay thì chạy `claude update`.

> **Phiên bản quan trọng:** Opus 5.5 cần từ v2.1.280, Fable cần từ v2.1.257. Chạy `claude --version`;
> nếu thấp hơn thì `claude update`.

**VS Code:** cài extension *Claude Code* từ Marketplace. Extension và CLI dùng chung cấu hình `~/.claude/` và `.claude/`.

## 3. Đăng nhập
Chạy `claude`, trình duyệt sẽ mở để đăng nhập. Nếu đặt biến môi trường `ANTHROPIC_API_KEY`, Claude Code hỏi một lần để dùng key đó
(tính tiền theo token trên Console thay vì theo gói). Đổi tài khoản bằng `/login`, `/logout`. Kiểm tra bằng `/status`.

## 4. Mở project này

```bash
git clone <url-repo> && cd <repo>

# Tạo môi trường Python cho máy local (không cần GPU)
python -m venv .venv
# Windows:
.venv\Scripts\python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
.venv\Scripts\python -m pip install -r requirements-dev.txt
# macOS/Linux: thay .venv\Scripts\python bằng .venv/bin/python

# Kiểm tra: phải thấy "6 passed"
.venv\Scripts\python -m pytest -q

claude
```

Lần đầu mở, Claude Code hỏi bạn có **tin tưởng thư mục** (workspace trust) không. Project này có hooks chạy script Python,
nên hãy đọc qua `.claude/settings.json` và `.claude/hooks/` trước khi đồng ý. Đó là thói quen tốt với mọi repo lạ.

**Hooks gọi lệnh `python`.** Trên Windows, lệnh này thường có sẵn sau khi cài Python. Trên macOS/Linux nếu chỉ có
`python3`, hãy sửa `python` thành `python3` trong `.claude/settings.json`. Các hook chỉ dùng thư viện chuẩn, chạy được từ Python 3.8.

## 5. Kiểm tra mọi thứ đã nạp
Trong phiên Claude, chạy lần lượt:

| Lệnh | Bạn sẽ thấy |
|---|---|
| `/context` | Context đang chứa gì, trong đó phải có `CLAUDE.md` |
| `/hooks` | 4 hook của project (SessionStart, 2× PreToolUse, PostToolUse) |
| `/permissions` | Các quy tắc allow/ask/deny từ `.claude/settings.json` |
| Gõ `/` | Danh sách lệnh, gồm các skill `/dev-cycle`, `/prepare-train`... |
| `/memory` | Các file CLAUDE.md đang dùng, bật/tắt auto memory |

Thông điệp đầu tiên của phiên sẽ kèm "Bối cảnh project" (branch, file đang sửa, trích `PROGRESS.md`) do hook
`session_context.py` nạp vào.

## 6. Cấu trúc thư mục cấu hình

```
~/.claude/                     # của riêng bạn, áp dụng mọi project
├── settings.json              # settings cá nhân (model, permissions, hooks...)
├── CLAUDE.md                  # chỉ dẫn cá nhân cho mọi project
├── agents/  skills/  rules/   # subagent / skill / rule cá nhân
└── projects/<project>/        # transcript các phiên (*.jsonl) + auto memory

<repo>/                        # của project, commit lên git để cả nhóm dùng chung
├── CLAUDE.md
├── .claude/settings.json      # permissions + hooks chung
├── .claude/settings.local.json  # ghi đè cá nhân, KHÔNG commit
├── .claude/agents/  .claude/skills/  .claude/rules/  .claude/hooks/
└── .mcp.json                  # (tùy chọn) MCP server chung
```

## 7. Nếu bắt đầu project mới của riêng bạn
Chạy `/init` trong thư mục project. Claude đọc code và sinh `CLAUDE.md` khởi đầu. Sau đó rút gọn nó còn những gì
Claude không tự suy ra được (lệnh build/test, quy ước riêng, bẫy thường gặp). Mục tiêu là dưới 200 dòng.
