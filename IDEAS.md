# IDEAS: backlog thí nghiệm

`experiment-analyst` thêm ý tưởng sau mỗi lần phân tích; `/idea-loop` chọn ý tưởng `đề xuất` có ưu tiên cao nhất để làm.
Ưu tiên: **config-only + rẻ** trước, **sửa code + tốn GPU** sau. Mỗi ý tưởng phải có giả thuyết kiểm chứng được.

Trạng thái: `đề xuất` → `đang làm` → `đã hiện thực (<commit>)` → `đã chạy (<run>)` / `bỏ (<lý do>)`

| # | Ý tưởng | Giả thuyết | Loại | Chi phí GPU (ước tính) | Ưu tiên | Trạng thái |
|---|---|---|---|---|---|---|
| 1 | Chạy baseline `configs/base.yaml` | Có mốc để so sánh mọi ý tưởng khác | config-only | ~10 phút T4 | cao | đề xuất |
| 2 | Label smoothing 0.1 (`train.label_smoothing=0.1`) | Giảm overconfidence, kỳ vọng val_acc tăng nhẹ | config-only | ~10 phút | cao | đề xuất |
| 3 | Tăng width 32 → 64 (`model.width=64`) | Model lớn hơn, bớt underfit | config-only | ~20 phút | trung bình | đề xuất |
| 4 | ResNet18 (`model.name=resnet18`) | Kiến trúc sâu hơn, kỳ vọng val_acc tăng rõ nhưng tốn GPU hơn | config-only | ~60 phút | trung bình | đề xuất |
| 5 | Thêm Mixup vào vòng train | Regularize mạnh, giảm gap train-val | sửa code | ~15 phút | thấp | đề xuất |
