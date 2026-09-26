"""(Tùy chọn) Đẩy tiến độ train lên một branch git riêng (mặc định `runs`) để Claude Code ở máy local đọc được.

Trên branch chỉ có file text nhỏ, mỗi run một thư mục:
    <run>/progress.json    trạng thái, epoch/step, val_acc, ETA, updated_at (UTC)
    <run>/metrics.csv      mỗi epoch một dòng
    <run>/summary.json     khi run xong
    <run>/train_tail.log   200 dòng log cuối (có traceback nếu lỗi)
Không bao giờ đẩy checkpoint. Lỗi mạng/git chỉ in cảnh báo, không làm dừng việc train.
Ở máy local: `python scripts/sync_runs.py` (hoặc skill /run-status) kéo branch này về thư mục runs/.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

PUSHED_FILES = ("progress.json", "metrics.csv", "summary.json")
TAIL_LINES = 200
MAX_FAILURES = 3


class NullLogger:
    """Dùng khi không bật --log-branch: mọi lời gọi đều không làm gì."""

    def update(self, **fields):
        pass

    def push(self, message):
        pass

    def maybe_push(self, message):
        pass

    def finish(self, status, error=None):
        pass

    def close(self):
        pass


class _Tee:
    """Ghi log ra console như cũ, đồng thời chép vào train.log để đẩy phần đuôi lên git."""

    def __init__(self, stream, fileobj):
        self.stream, self.file = stream, fileobj

    def write(self, s):
        self.stream.write(s)
        self.file.write(s)
        return len(s)

    def flush(self):
        self.stream.flush()
        self.file.flush()

    def __getattr__(self, name):
        return getattr(self.stream, name)


class RunLogger:
    def __init__(self, run_name, ckpt_dir, branch="runs", remote=None, every_min=10.0, workdir=None):
        self.run_name, self.ckpt_dir, self.branch = run_name, ckpt_dir, branch
        self.every_s = every_min * 60
        self.work = workdir or os.path.join(tempfile.gettempdir(), f"runlog-{run_name}")
        self.progress = {"run_name": run_name, "status": "starting", "push_every_min": every_min}
        self.last_push = 0.0
        self.failures = 0
        self.enabled = True
        self._log_file = open(os.path.join(ckpt_dir, "train.log"), "a", encoding="utf-8")
        self._stdout, self._stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = _Tee(sys.stdout, self._log_file), _Tee(sys.stderr, self._log_file)
        try:
            self.remote = remote or self._git("remote", "get-url", "origin", cwd=os.getcwd()).stdout.strip()
            self._init_repo()
            print(f"[runlog] đẩy tiến độ lên branch '{branch}' mỗi {every_min:g} phút")
        except Exception as e:
            self.enabled = False
            print(f"[runlog] tắt đẩy log: {e}")

    # ---- git ----
    def _git(self, *args, cwd=None, check=True):
        env = dict(os.environ, GIT_TERMINAL_PROMPT="0")   # thiếu token thì báo lỗi ngay, không treo chờ nhập mật khẩu
        r = subprocess.run(["git", *args], cwd=cwd or self.work, env=env, capture_output=True, text=True, timeout=120)
        if check and r.returncode != 0:
            raise RuntimeError(f"git {args[0]}: {r.stderr.strip()[-300:]}")
        return r

    def _init_repo(self):
        if not os.path.isdir(os.path.join(self.work, ".git")):
            os.makedirs(self.work, exist_ok=True)
            self._git("init", "-q")
            self._git("remote", "add", "origin", self.remote)
            self._git("symbolic-ref", "HEAD", f"refs/heads/{self.branch}")
        self._sync_with_remote()

    def _sync_with_remote(self):
        # Lấy bản mới nhất của branch (nếu remote đã có) để commit của mình nằm trên đó.
        if self._git("fetch", "-q", "origin", self.branch, check=False).returncode == 0:
            self._git("reset", "-q", "--hard", "FETCH_HEAD")

    def _commit(self, message):
        dest = os.path.join(self.work, self.run_name)
        os.makedirs(dest, exist_ok=True)
        for name in PUSHED_FILES:
            src = os.path.join(self.ckpt_dir, name)
            if os.path.isfile(src):
                shutil.copy(src, dest)
        sys.stdout.flush()
        with open(os.path.join(self.ckpt_dir, "train.log"), encoding="utf-8", errors="replace") as f:
            tail = f.readlines()[-TAIL_LINES:]
        with open(os.path.join(dest, "train_tail.log"), "w", encoding="utf-8") as f:
            f.writelines(tail)
        self._git("add", "-A", self.run_name)
        if self._git("diff", "--cached", "--quiet", check=False).returncode == 0:
            return False
        self._git("-c", "user.name=run-logger", "-c", "user.email=run-logger@localhost",
                  "commit", "-q", "-m", f"log({self.run_name}): {message}")
        return True

    # ---- API dùng trong src/train.py ----
    def update(self, **fields):
        self.progress.update(fields)

    def push(self, message):
        self.progress["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with open(os.path.join(self.ckpt_dir, "progress.json"), "w", encoding="utf-8") as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)
        if not self.enabled:
            return
        try:
            if not self._commit(message):
                return
            for _ in range(3):
                if self._git("push", "-q", "origin", f"HEAD:refs/heads/{self.branch}", check=False).returncode == 0:
                    self.last_push, self.failures = time.time(), 0
                    return
                # Bị từ chối: branch vừa có commit mới (run khác đẩy lên) → lấy bản mới, commit lại file của mình.
                self._sync_with_remote()
                self._commit(message)
            raise RuntimeError("push bị từ chối 3 lần")
        except Exception as e:
            self.failures += 1
            print(f"[runlog] không đẩy được log ({self.failures}/{MAX_FAILURES}): {e}")
            if self.failures >= MAX_FAILURES:
                self.enabled = False
                print("[runlog] tắt đẩy log cho phiên này. Việc train vẫn tiếp tục bình thường.")

    def maybe_push(self, message):
        if time.time() - self.last_push >= self.every_s:
            self.push(message)

    def finish(self, status, error=None):
        self.progress["status"] = status
        if error:
            self.progress["error"] = error[-3000:]
            self._log_file.write(error)          # traceback vào train_tail.log, không in lặp ra console
        self.push(status)

    def close(self):
        sys.stdout, sys.stderr = self._stdout, self._stderr
        self._log_file.close()
