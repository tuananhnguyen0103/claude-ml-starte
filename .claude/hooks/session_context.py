"""SessionStart hook: nạp bối cảnh project vào đầu mỗi phiên (startup / resume / sau /clear / sau /compact).

Với SessionStart, stdout dạng text được Claude Code thêm vào context. Nhờ vậy phiên mới, kể cả sau khi
hết giới hạn sử dụng, biết ngay: đang ở branch nào, file nào đang sửa dở, việc gì đang làm và run nào đang chạy.

Test tay (Git Bash):
  echo '{"source":"startup"}' | python .claude/hooks/session_context.py
"""
import json
import os
import re
import subprocess
import sys

SECTIONS = ("Đang làm", "Run đang chạy", "Bước tiếp theo")


def git(args, cwd):
    try:
        r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def progress_sections(path, max_lines=40):
    if not os.path.isfile(path):
        return []
    out, keep = [], False
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("## "):
                keep = any(line[3:].strip().startswith(s) for s in SECTIONS)
            if keep:
                out.append(line.rstrip())
    return [l for l in out if l.strip()][:max_lines]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raw = sys.stdin.buffer.read().decode("utf-8") or "{}"
    data = json.loads(raw)
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()

    lines = ["# Bối cảnh project (hook SessionStart, nguồn: %s)" % data.get("source", "?")]
    branch = git(["rev-parse", "--abbrev-ref", "HEAD"], root)
    if branch is None:
        lines.append("- Chưa phải git repo hoặc chưa có commit nào. Xem README mục Bắt đầu.")
    else:
        status = git(["status", "--short"], root) or ""
        changed = status.splitlines()
        lines.append("- Branch: %s | file thay đổi chưa commit: %d" % (branch, len(changed)))
        lines += ["    " + l for l in changed[:15]]
        log = git(["log", "--oneline", "-5"], root)
        if log:
            lines.append("- 5 commit gần nhất:")
            lines += ["    " + l for l in log.splitlines()]
    sections = progress_sections(os.path.join(root, "PROGRESS.md"))
    if sections:
        lines.append("- Trích PROGRESS.md:")
        lines += ["    " + re.sub(r"^#+\s*", "", l) if l.startswith("#") else "    " + l for l in sections]
    print("\n".join(lines))


if __name__ == "__main__":
    main()
