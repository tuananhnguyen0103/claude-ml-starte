---
name: dev-cycle
description: Quy trình phát triển chuẩn cho một task code theo thứ tự plan, implement, test, debug, review rồi commit, dùng đội subagent của project.
argument-hint: "<mô tả task>"
disable-model-invocation: true
---

# Dev cycle

**Task:** $ARGUMENTS

## Trạng thái repo lúc bắt đầu
!`git status --short || true`
!`git log --oneline -5 || true`

## Quy trình (làm tuần tự, không bỏ bước; bạn là người điều phối, giao việc cho subagent)

0. **Chuẩn bị.** Nếu task trống, hỏi người dùng. Nếu working tree đang có thay đổi không liên quan task, hỏi người dùng
   có commit/stash trước không. Cập nhật mục "Đang làm" trong `PROGRESS.md`.

1. **PLAN**: giao cho subagent `planner`, kèm task và bối cảnh cần thiết.
   - Bỏ qua bước này nếu task nhỏ: sửa 1 file, mô tả được bằng 1 câu.
   - Tóm tắt kế hoạch cho người dùng. **Dừng chờ duyệt** nếu kế hoạch ghi "cần RUN_NAME mới", chạm hơn 5 file,
     hoặc có giả định quan trọng. Các trường hợp khác thì tiếp tục.

2. **IMPLEMENT**: giao cho `implementer`, dán nguyên văn kế hoạch vào prompt.

3. **TEST**: giao cho `test-runner` (nếu có config mới, nêu tên file config).

4. **DEBUG** (chỉ khi FAIL): giao cho `debugger`, kèm nguyên văn báo cáo lỗi, rồi quay lại bước 3.
   Tối đa **3 vòng**. Quá 3 vòng: dừng, báo cáo những gì đã thử, **không commit**.

5. **REVIEW**: giao cho `code-reviewer`, kèm kế hoạch làm tiêu chí.
   - `BLOCKER`: giao `implementer` hoặc `debugger` sửa, rồi quay lại bước 3.
   - `SHOULD-FIX`: sửa nếu nhỏ, còn lại ghi vào `PROGRESS.md` mục ghi chú.

6. **COMMIT**: cập nhật `PROGRESS.md`, rồi commit với message dạng conventional:
   `feat:` / `fix:` / `exp:` / `test:` / `docs:` / `chore:`. **Không push**: push là việc của `/prepare-train`.

7. **Báo cáo cuối** cho người dùng:
   - Thay đổi chính (2–4 dòng)
   - Bằng chứng: dòng tóm tắt pytest và smoke
   - Commit hash
   - Bước tiếp theo, ví dụ `/prepare-train run-00X-<tên> <config>`
