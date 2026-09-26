---
name: idea-loop
description: Vòng phát triển ý tưởng tự động, gồm phân tích kết quả mới, chọn ý tưởng ưu tiên cao nhất trong IDEAS.md, hiện thực nó và chuẩn bị sẵn run tiếp theo (không tự push).
argument-hint: "[auto]  (auto = tự chọn ý tưởng, không hỏi)"
disable-model-invocation: true
---

# Idea loop

**Chế độ:** $ARGUMENTS (trống = hỏi người dùng trước khi chọn ý tưởng)

## Backlog hiện tại
!`cat IDEAS.md || true`

## Kết quả đã có
!`python scripts/compare_runs.py || true`

## Quy trình

1. **Cập nhật kết quả.** Nếu `results/` hoặc `runs/` có run mà `EXPERIMENTS.md` chưa điền best val_acc, chạy skill `analyze-runs` trước.
2. **Chọn một ý tưởng** trạng thái `đề xuất`, theo thứ tự ưu tiên:
   ưu tiên cao → config-only → chi phí GPU thấp. Baseline luôn phải chạy trước mọi ý tưởng khác.
   - Chế độ thường: trình bày lựa chọn kèm lý do và 1 phương án thay thế, hỏi người dùng (một câu hỏi).
   - Chế độ `auto`: chọn luôn và ghi lý do.
   Đổi trạng thái ý tưởng thành `đang làm`.
3. **Hiện thực:**
   - Config-only: dùng skill `new-experiment`.
   - Cần sửa code: đọc `.claude/skills/dev-cycle/SKILL.md` và làm đúng quy trình đó, với task là ý tưởng đã chọn.
4. **Cập nhật** `IDEAS.md` thành `đã hiện thực (<commit hoặc file config>)`.
5. **Dừng trước khi push.** Đề xuất lệnh `/prepare-train run-<số tiếp theo>-<tên> <config>` để người dùng chạy khi sẵn sàng.
   Push và dùng GPU là quyết định của con người.
6. **Báo cáo:** ý tưởng đã chọn, đã làm gì, bằng chứng test, lệnh tiếp theo.
