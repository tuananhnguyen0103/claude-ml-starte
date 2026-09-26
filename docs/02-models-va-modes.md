# 02 · Model, effort, fast mode và chế độ quyền

Có bốn "núm vặn" độc lập, cần phân biệt rõ:

| Núm | Quyết định điều gì | Lệnh |
|---|---|---|
| **Model** | Trí tuệ nền, tốc độ, chi phí | `/model` |
| **Effort** | Model suy nghĩ sâu tới đâu trước khi trả lời/hành động | `/effort`, `Alt+T` |
| **Fast mode** | Cùng model Opus nhưng trả lời nhanh hơn, giá cao hơn | `/fast` |
| **Permission mode** | Claude được tự làm gì mà không hỏi bạn | `Shift+Tab` |

## 1. Các model (09/2026)

| Model | Alias | Dùng khi | Giá API ($/1M token vào/ra) | Context |
|---|---|---|---|---|
| **Claude Fable 5.1** | `fable` (`best` trỏ tới nó nếu có) | Mạnh nhất: suy luận khó, task dài nhiều giờ, kiểm chứng. Phải chọn thủ công, cần v2.1.257+ | 10 / 50 | 1M |
| **Claude Opus 5.5** | `opus` | **Mặc định** cho Pro/Max/Team/Enterprise. Lập trình phức tạp, lập kế hoạch, debug. Cần v2.1.280+ | 4 / 20 | 1M |
| **Claude Sonnet 5** | `sonnet` | Code hằng ngày, viết code theo kế hoạch có sẵn, nhanh và rẻ hơn Opus | 2 / 10 | 1M |
| **Claude Haiku 4.5** | `haiku` | Nhanh nhất, rẻ nhất: chạy test, tra cứu đơn giản, subagent phụ | 1 / 5 | 200K |

- Alias đặc biệt: `default` (về mặc định của tài khoản), `opusplan` (Opus khi ở plan mode, Sonnet khi thực thi).
- Với **gói thuê bao** (Pro/Max...), bạn không trả theo token, nhưng model lớn tiêu **hạn mức sử dụng** nhanh hơn.
  Giá API ở trên giúp hình dung tỉ lệ chi phí giữa các model.

### Đặt model: thứ tự ưu tiên (cao → thấp)
1. `/model <alias>` trong phiên. Lựa chọn được lưu làm mặc định vào `~/.claude/settings.json`.
   Trong bảng chọn `/model`, nhấn `s` để chỉ đổi cho phiên này.
2. `claude --model opus` khi khởi động (chỉ phiên đó).
3. Biến môi trường `ANTHROPIC_MODEL=sonnet`.
4. `"model": "opus"` trong file settings.

Phiên được resume (`--continue`/`--resume`) giữ model cũ của nó. `/status` cho biết model đang dùng.

### Model cho subagent
Thứ tự ưu tiên: model Claude truyền khi gọi → trường `model:` trong file agent → biến `CLAUDE_CODE_SUBAGENT_MODEL`
→ model của phiên chính. Đội agent của project này đặt sẵn: `planner`/`debugger` dùng opus, `implementer`/`code-reviewer`/
`experiment-analyst` dùng sonnet, `test-runner` dùng haiku.

## 2. Effort: mức độ suy nghĩ

| Mức | Đặc điểm |
|---|---|
| `low` | Nhanh, ít token. Hợp với việc đơn giản, subagent chạy lệnh |
| `medium` | **Mặc định của Opus 5.5.** Cân bằng, tiết kiệm |
| `high` | Mặc định của Sonnet 5, Fable, Opus 5. Hợp với phần lớn việc lập trình |
| `xhigh` | Suy luận sâu hơn, tốn token hơn |
| `max` | Sâu nhất; có thể không đáng chi phí tăng thêm |
| `ultracode` | `xhigh` cộng điều phối workflow động cho task rất lớn |

Cách đặt:
- `/effort` mở thanh trượt; `/effort high` đặt thẳng; `/effort auto` xóa lựa chọn đã lưu.
- `Alt+T` (macOS: `Option+T`) đổi cho phiên hiện tại. Cờ `claude --effort xhigh` khi khởi động.
- Settings: `"effortLevel": "high"`, hoặc theo từng model: `"modelSettings": {"opus": {"effort": "xhigh"}}`.
- **`ultrathink`**: gõ từ này ở bất kỳ đâu trong prompt để yêu cầu suy nghĩ sâu hơn **cho riêng lượt đó**, không đổi
  mức effort của phiên. Các cụm như "think hard" chỉ là chữ bình thường.
- Subagent và skill có thể đặt `effort:` riêng trong frontmatter (xem `test-runner.md`: `effort: low`).

**Chọn nhanh cho project này:** hỏi đáp và sửa nhỏ dùng Opus 5.5 `medium`. Thiết kế hoặc debug lỗi resume khó dùng
`high`/`xhigh`, hoặc thêm `ultrathink` vào prompt. Chạy test thì để Haiku `low` qua subagent.

## 3. Fast mode
- Cùng model Opus (5.5, 5 hoặc 4.8), trả lời **nhanh tới khoảng 2.5 lần**, giá mỗi token cao hơn (Opus 5.5: $8/$40, gấp đôi giá thường).
- Bật/tắt bằng `/fast`. Khi bật, cạnh ô nhập hiện biểu tượng `↯`.
- Với gói thuê bao, fast mode **trả bằng usage credits** (phải bật trong Settings > Usage trên claude.ai),
  không tính vào hạn mức của gói.
- Nên bật ngay từ đầu phiên. Bật giữa phiên dài thì toàn bộ context phải tính lại theo giá fast một lần.
- Hợp với debug trực tiếp hay lặp nhanh. Không nên dùng cho task tự động dài hoặc CI.

## 4. Permission mode: Claude tự làm được gì

| Mode | Chạy không cần hỏi | Hợp với |
|---|---|---|
| **Manual** (`default`) | Chỉ đọc | Việc nhạy cảm, codebase lạ |
| `acceptEdits` | Đọc, sửa file, lệnh file cơ bản (`mkdir`, `mv`, `cp`...) | Lặp code khi bạn vẫn review diff |
| `plan` | Chỉ đọc và lập kế hoạch; **không sửa** cho tới khi bạn duyệt plan | Khám phá trước khi đổi |
| `auto` | Mọi thứ, có **model phân loại** chạy nền chặn hành động rủi ro | Task dài, bớt hỏi quyền |
| `dontAsk` | Chỉ những gì được allow sẵn, còn lại tự từ chối | CI, script |
| `bypassPermissions` | Mọi thứ, không kiểm tra | **Chỉ** trong container/VM cô lập |

- **Đổi mode trong phiên:** `Shift+Tab` (trên một số máy Windows là `Alt+M`). Từ `auto`, vòng lặp là
  Manual → acceptEdits → plan → (auto nếu có). Thanh trạng thái hiện `⏸ plan mode on`, `⏵⏵ accept edits on`...
- **Khi khởi động:** `claude --permission-mode plan`. Mặc định cho mọi phiên đặt ở `permissions.defaultMode` trong settings.
  Lưu ý: settings **của project** không được đặt `auto` hay `bypassPermissions` làm mặc định, để một repo lạ không tự nâng quyền.
- **Mode khởi đầu:** từ v2.1.283 là `auto` cho terminal và VS Code. Bản cũ hơn chỉ dùng `auto` trên Pro/Max/Team, còn lại là Manual.
  `claude -p` (headless) luôn bắt đầu ở Manual.
- **Luôn đúng ở mọi mode:** quy tắc `deny` luôn chặn, kể cả trong bypass. Quy tắc `ask` luôn hỏi.
  Vì vậy project này đặt `git push` là `ask` (xem [04](04-harness.md)).

### Plan mode: quy trình khuyến nghị cho thay đổi lớn
1. `Shift+Tab` tới `⏸ plan mode on`, hoặc gõ `/plan <mô tả>` cho một prompt.
2. *"Đọc src/train.py và src/data.py. Tôi muốn thêm Mixup. Cần sửa file nào, ảnh hưởng resume ra sao? Lập kế hoạch."*
3. `Ctrl+G` mở plan trong editor để sửa tay.
4. Duyệt plan. Claude chuyển sang mode thực thi và bắt đầu code.
5. Task nhỏ mô tả được bằng một câu thì bỏ qua plan mode, vì nó tốn thêm công.

## 5. Theo dõi chi phí và context
- `/usage` (alias `/cost`): token và chi phí đã dùng. `/status`: model, tài khoản, cách đăng nhập.
- `/context`: lưới màu cho thấy phần nào đang chiếm context.
- Cách tiết kiệm hiệu quả nhất: `/clear` giữa các task không liên quan, và giao việc đọc nhiều file cho subagent
  (subagent đọc trong context riêng, chỉ trả về bản tóm tắt).
