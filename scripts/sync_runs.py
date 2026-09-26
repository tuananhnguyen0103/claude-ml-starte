"""Kéo log các run từ branch `runs` (do Colab/Kaggle đẩy lên) về thư mục runs/ (gitignored) và in bảng tiến độ.

Không đổi branch đang làm việc, không đụng working tree: chỉ `git fetch` rồi đọc file bằng `git show`.
Chạy: python scripts/sync_runs.py [--branch runs] [--remote origin]
Chỉ dùng thư viện chuẩn, chạy được bằng Python 3.8+.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, timeout=120)


def age_minutes(iso):
    try:
        return (datetime.now(timezone.utc) - datetime.fromisoformat(iso)).total_seconds() / 60
    except (TypeError, ValueError):
        return None


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser()
    p.add_argument("--branch", default="runs")
    p.add_argument("--remote", default="origin")
    p.add_argument("--dest", default="runs")
    args = p.parse_args(argv)

    ref = f"refs/remotes/{args.remote}/{args.branch}"
    r = git("fetch", "-q", args.remote, f"+refs/heads/{args.branch}:{ref}")
    if r.returncode != 0:
        print(f"Chưa lấy được branch '{args.branch}' từ '{args.remote}': "
              f"{r.stderr.decode('utf-8', 'replace').strip()[-200:]}")
        print("→ Colab chưa đẩy log lần nào (LOG_BRANCH trống?), hoặc token thiếu quyền ghi, hoặc chưa có remote.")
        return

    files = git("ls-tree", "-r", "--name-only", ref).stdout.decode("utf-8").splitlines()
    dest = Path(args.dest)
    for name in files:
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(git("show", f"{ref}:{name}").stdout)
    last = git("log", "-1", "--format=%cr: %s", ref).stdout.decode("utf-8").strip()
    print(f"Đã đồng bộ {len(files)} file từ {args.remote}/{args.branch} → {dest}/ (commit cuối {last})\n")

    runs = sorted(d for d in dest.iterdir() if (d / "progress.json").exists()) if dest.exists() else []
    if not runs:
        print("Branch chưa có progress.json nào.")
        return
    print("| run | trạng thái | epoch | val_acc | best | ETA (phút) | cập nhật | nền tảng / GPU |")
    print("|---|---|---|---|---|---|---|---|")
    warnings = []
    for d in runs:
        pr = json.loads((d / "progress.json").read_text(encoding="utf-8"))
        age = age_minutes(pr.get("updated_at"))
        age_txt = "?" if age is None else f"{age:.0f} phút trước"
        status = pr.get("status", "?")
        print(f"| {d.name} | {status} | {pr.get('epoch', '?')}/{pr.get('total_epochs', '?')} | {pr.get('val_acc', '-')} "
              f"| {pr.get('best_val_acc', '-')} | {pr.get('eta_min', '-')} | {age_txt} "
              f"| {pr.get('platform', '?')} / {pr.get('gpu', '?')} |")
        limit = 2 * float(pr.get("push_every_min", 10)) + 10
        if status == "running" and age is not None and age > limit:
            warnings.append(f"- {d.name}: 'running' nhưng {age:.0f} phút không cập nhật (> {limit:.0f}) → "
                            "có thể phiên đã bị ngắt. Mở notebook, Run all với cùng RUN_NAME để resume.")
        if status == "error":
            last_line = pr.get("error", "").strip().splitlines()[-1:] or ["(không có traceback)"]
            warnings.append(f"- {d.name}: LỖI → {last_line[0]}  (chi tiết: {d / 'train_tail.log'})")
        if status == "stopped-time-budget":
            warnings.append(f"- {d.name}: đã dừng sạch vì hết time budget → chạy lại notebook với cùng RUN_NAME.")
    if warnings:
        print("\nCần chú ý:")
        print("\n".join(warnings))


if __name__ == "__main__":
    main()
