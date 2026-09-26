"""Test luồng train ở chế độ --smoke (CPU, dữ liệu giả). Chạy: python -m pytest -q"""
import json

import torch

from src import train
from src.config import load_config
from src.utils.checkpoint import latest_ckpt, load_ckpt, save_ckpt


def run(ckpt_dir, *extra):
    train.main(["--smoke", "--config", "configs/base.yaml", "--ckpt-dir", str(ckpt_dir),
                "--data-dir", str(ckpt_dir / "data"), *extra])


def test_smoke_runs_to_completion(tmp_path):
    run(tmp_path)
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["epochs"] == 2 and summary["steps"] == 8
    assert (tmp_path / "best.pt").exists()
    assert len((tmp_path / "metrics.csv").read_text(encoding="utf-8").strip().splitlines()) == 3  # header + 2 epoch


def test_resume_continues_from_checkpoint(tmp_path):
    run(tmp_path, "--max-steps", "3")                 # giả lập phiên Colab bị ngắt giữa epoch 1
    s = load_ckpt(latest_ckpt(tmp_path))
    assert (s["epoch"], s["step"]) == (0, 3)
    run(tmp_path)                                      # phiên mới: tự tìm ckpt và train tiếp
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["steps"] == 8


def test_resume_gives_same_weights_as_uninterrupted(tmp_path):
    """Resume đúng nghĩa: bị ngắt rồi chạy tiếp phải cho ra đúng model như chạy một mạch."""
    run(tmp_path / "a")
    run(tmp_path / "b", "--max-steps", "3")
    run(tmp_path / "b")
    wa = load_ckpt(latest_ckpt(tmp_path / "a"))["model"]
    wb = load_ckpt(latest_ckpt(tmp_path / "b"))["model"]
    for k in wa:
        assert torch.allclose(wa[k].float(), wb[k].float(), atol=1e-6), k


def test_finished_run_is_not_retrained(tmp_path, capsys):
    run(tmp_path)
    run(tmp_path)
    assert "[done] Run này đã train xong" in capsys.readouterr().out


def test_save_ckpt_keeps_last_and_leaves_no_tmp(tmp_path):
    for step in range(1, 5):
        save_ckpt(tmp_path, {"step": step}, keep_last=2)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["step_00000003.pt", "step_00000004.pt"]


def test_config_override_parses_types():
    cfg = load_config("configs/base.yaml", ["train.lr=0.05", "model.name=resnet18", "data.augment=false"])
    assert cfg["train"]["lr"] == 0.05
    assert cfg["model"]["name"] == "resnet18"
    assert cfg["data"]["augment"] is False
