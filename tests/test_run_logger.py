"""Test luồng đẩy log lên branch `runs`, dùng một bare repo local đóng vai GitHub (không cần mạng, không cần token)."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from src import train
from src.utils.run_logger import RunLogger

ROOT = Path(__file__).resolve().parent.parent


def git(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=True).stdout


@pytest.fixture
def remote(tmp_path):
    path = tmp_path / "origin.git"
    git("init", "-q", "--bare", str(path))
    return path


def run(tmp_path, remote, run_name, *extra):
    train.main(["--smoke", "--run-name", run_name, "--ckpt-dir", str(tmp_path / "ckpt" / run_name),
                "--log-branch", "runs", "--log-remote", str(remote), "--log-every-min", "0",
                "--log-workdir", str(tmp_path / "work" / run_name), *extra])


def progress(remote, run_name):
    return json.loads(git("--git-dir", str(remote), "show", f"runs:{run_name}/progress.json"))


def test_pushes_progress_metrics_and_log_tail(tmp_path, remote):
    run(tmp_path, remote, "run-a")
    pr = progress(remote, "run-a")
    assert pr["status"] == "done" and pr["epoch"] == pr["total_epochs"] == 2
    files = git("--git-dir", str(remote), "ls-tree", "-r", "--name-only", "runs").split()
    assert set(files) == {"run-a/progress.json", "run-a/metrics.csv", "run-a/summary.json", "run-a/train_tail.log"}
    assert not any(f.endswith(".pt") for f in files)             # không bao giờ đẩy checkpoint
    assert "[done]" in git("--git-dir", str(remote), "show", "runs:run-a/train_tail.log")


def test_interrupted_run_then_resume_updates_status(tmp_path, remote):
    run(tmp_path, remote, "run-b", "--max-steps", "3")
    assert progress(remote, "run-b")["status"] == "stopped-time-budget"
    run(tmp_path, remote, "run-b")
    assert progress(remote, "run-b")["status"] == "done"


def test_crash_pushes_traceback(tmp_path, remote):
    with pytest.raises(ValueError):
        run(tmp_path, remote, "run-c", "--set", "model.name=vgg")
    pr = progress(remote, "run-c")
    assert pr["status"] == "error" and "Model không hỗ trợ" in pr["error"]


def test_two_runs_pushing_to_same_branch(tmp_path, remote):
    """Run thứ hai đẩy sau khi branch đã có commit mới: phải tự lấy bản mới rồi đẩy lại, không mất log của run kia."""
    for name in ("run-x", "run-y"):
        (tmp_path / name).mkdir()
    a = RunLogger("run-x", str(tmp_path / "run-x"), remote=str(remote), workdir=str(tmp_path / "wx"))
    b = RunLogger("run-y", str(tmp_path / "run-y"), remote=str(remote), workdir=str(tmp_path / "wy"))
    try:
        a.finish("done")
        b.finish("done")                                      # bị từ chối lần đầu vì branch đã có commit của run-x
    finally:
        b.close()
        a.close()
    files = git("--git-dir", str(remote), "ls-tree", "-r", "--name-only", "runs").split()
    assert "run-x/progress.json" in files and "run-y/progress.json" in files


def test_missing_remote_does_not_break_training(tmp_path):
    run(tmp_path, tmp_path / "khong-ton-tai.git", "run-d")         # vẫn train xong, chỉ in cảnh báo
    assert json.loads((tmp_path / "ckpt" / "run-d" / "progress.json").read_text(encoding="utf-8"))["status"] == "done"


def test_sync_runs_mirrors_branch_into_runs_dir(tmp_path, remote):
    run(tmp_path, remote, "run-e")
    local = tmp_path / "local"
    git("clone", "-q", str(remote), str(local))
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "sync_runs.py")], cwd=local,
                         capture_output=True, timeout=120).stdout.decode("utf-8")
    assert (local / "runs" / "run-e" / "metrics.csv").exists()
    assert "| run-e | done | 2/2 |" in out
