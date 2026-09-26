# CLAUDE.md

Project mẫu để học Claude Code: train CNN phân loại ảnh CIFAR-10. Code được viết ở máy cá nhân (không có GPU),
push lên GitHub, rồi train trên Google Colab hoặc Kaggle. Tài liệu cho người học nằm trong `docs/`
(bắt đầu từ `docs/00-lo-trinh.md`). File này là chỉ dẫn cho Claude.

## Lệnh
- Python của project: `.venv/Scripts/python` (Windows) hoặc `.venv/bin/python` (macOS/Linux), dưới đây viết tắt là `PY`.
- Test: `PY -m pytest -q`
- Smoke train (CPU, dữ liệu giả, vài giây): `PY -m src.train --smoke --ckpt-dir checkpoints/smoke --resume none`
- Sinh lại notebook sau khi sửa `scripts/make_notebooks.py`: `PY scripts/make_notebooks.py`
- Kéo log run từ branch `runs` (Colab/Kaggle đẩy lên) về `runs/`: `python scripts/sync_runs.py`
- So sánh kết quả các run (`results/` + `runs/`): `python scripts/compare_runs.py`
- Máy local không có GPU: không chạy train thật (thiếu `--smoke`) ở local.

## Cấu trúc
- `src/train.py`: entrypoint (resume, time budget, checkpoint, metrics). `src/data.py`, `src/model.py`, `src/config.py`.
- `src/utils/`: checkpoint, env (local/colab/kaggle), metrics, hub_sync (tùy chọn, HF Hub),
  run_logger (tùy chọn `--log-branch`: đẩy tiến độ lên branch `runs`; lỗi git không được làm dừng train).
- `configs/base.yaml` là baseline. Mỗi thí nghiệm là một file `configs/exp_<tên>.yaml`.
- `notebooks/*.ipynb` được **sinh tự động** từ `scripts/make_notebooks.py`, không sửa trực tiếp.
- `results/<run>/`: kết quả tải tay (được commit). `runs/<run>/`: bản sao branch git `runs` do Colab đẩy lên (gitignored).
  Không bao giờ commit vào branch `runs` từ máy local; branch đó chỉ do `src/utils/run_logger.py` ghi.
- `PROGRESS.md` là trạng thái công việc, `EXPERIMENTS.md` là nhật ký run, `IDEAS.md` là backlog thí nghiệm.

## Quy tắc bắt buộc
1. Không commit data, checkpoint (`*.pt`...), secret, hay file > 5 MB (hook `guard_bash` chặn).
2. Chạy test và smoke trước khi commit code train. Chỉ commit khi cả hai pass.
3. Chỉ push khi người dùng yêu cầu hoặc khi đang chạy `/prepare-train`. Không bao giờ force push.
4. Giữ khả năng resume: `tests/test_train.py::test_resume_gives_same_weights_as_uninterrupted` phải pass.
5. Không hardcode `/content`, `/kaggle` trong `src/`. Đường dẫn đi qua CLI hoặc `src/utils/env.py`.
6. Không thêm `torch`/`torchvision` vào `requirements.txt`.
7. Nếu thay đổi làm checkpoint cũ không dùng được (kiến trúc, số lớp, optimizer, `train.epochs`, `train.batch_size`),
   phải báo rõ và đề xuất `RUN_NAME` mới.
8. Khi người dùng dán lỗi từ Colab/Kaggle, làm theo quy trình của `/fix-remote-error` (giao cho `debugger`).
9. Cuối mỗi phần việc, cập nhật `PROGRESS.md` (Đang làm / Run đang chạy / Bước tiếp theo).

## Đội subagent (`.claude/agents/`)
| Việc | Giao cho |
|---|---|
| Lập kế hoạch cho task nhiều file hoặc ý tưởng mới | `planner` |
| Viết code theo kế hoạch | `implementer` |
| Chạy test/smoke sau khi sửa code | `test-runner` |
| Test fail, traceback, lỗi từ Colab/Kaggle | `debugger` |
| Review trước mỗi commit | `code-reviewer` |
| Có kết quả run mới, hoặc cần ý tưởng | `experiment-analyst` |

Subagent không thấy hội thoại. Khi giao việc, đưa đủ bối cảnh: task, kế hoạch, lỗi nguyên văn.
Quy trình trọn vòng: `/dev-cycle`, `/prepare-train`, `/fix-remote-error`, `/analyze-runs`, `/new-experiment`, `/idea-loop`.
Hỏi về tiến độ run đang train → skill `run-status` (đọc log từ branch `runs`, không bắt người dùng dán log).

## Git
- Commit message: `feat:` / `fix:` / `exp:` / `test:` / `docs:` / `chore:`. Nhánh `main` luôn chạy được.
- Mỗi run dài có tag `run-XXX-<mô-tả>` (do `/prepare-train` tạo), notebook checkout đúng tag đó.

## Khi compact
Giữ lại: task đang làm, danh sách file đã sửa, lệnh test, `RUN_NAME`/`REF` đang dùng, lỗi chưa giải quyết.
