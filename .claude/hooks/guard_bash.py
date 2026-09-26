"""PreToolUse hook (Bash | PowerShell): chặn các lệnh nguy hiểm với project này.

Claude Code gửi JSON qua stdin, ví dụ {"tool_name": "Bash", "tool_input": {"command": "..."}, "cwd": "..."}.
Hook in ra JSON permissionDecision="deny" kèm lý do → lệnh không chạy, Claude đọc lý do và tự sửa cách làm.

Chặn:
  1. git push --force / -f / +refspec (mất lịch sử của người khác)
  2. git add -f (bỏ qua .gitignore)
  3. git add / git commit chứa data, checkpoint, secret hoặc file > 5 MB
  4. lệnh in secret ra màn hình (cat .env, echo $HF_TOKEN ...)

Test tay (Git Bash):
  echo '{"tool_name":"Bash","tool_input":{"command":"git push -f origin main"}}' | python .claude/hooks/guard_bash.py
"""
import json
import os
import re
import shlex
import subprocess
import sys

FORBIDDEN = re.compile(
    r"(^|/)(data|checkpoints|ckpt|outputs|wandb)/"
    r"|\.(pt|pth|ckpt|safetensors|onnx|bin|zip)$"
    r"|(^|/)(\.env(\..*)?|kaggle\.json|.*\.pem)$"
)
MAX_MB = 5
SECRET_FILES = r"(\.env\b|kaggle\.json)"
SECRET_VARS = r"(GITHUB_TOKEN|HF_TOKEN|ANTHROPIC_API_KEY)"


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def git(args, cwd):
    try:
        return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return ""


def check_files(paths, cwd):
    bad = []
    for p in paths:
        p = p.replace("\\", "/")
        full = os.path.join(cwd, p)
        if FORBIDDEN.search(p):
            bad.append(p)
        elif os.path.isfile(full) and os.path.getsize(full) > MAX_MB * 1024 * 1024:
            bad.append(p + " (> %d MB)" % MAX_MB)
    return bad


def main():
    data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    cmd = data.get("tool_input", {}).get("command", "")
    cwd = data.get("cwd") or os.getcwd()
    segments = re.split(r"&&|\|\||;|\|", cmd)

    if re.search(r"\bgit\s+push\b", cmd) and re.search(r"(\s--force(-with-lease)?\b|\s-f\b|\s\+\S)", cmd):
        deny("Force push bị cấm trong project này (ghi đè lịch sử trên GitHub). "
             "Nếu cần sửa commit đã push, tạo commit mới thay vì viết lại lịch sử.")

    to_be_added = []
    for seg in segments:
        m = re.match(r"\s*git\s+add\b(.*)", seg)
        if not m:
            continue
        try:
            args = shlex.split(m.group(1))
        except ValueError:
            args = m.group(1).split()
        if "-f" in args or "--force" in args:
            deny("`git add -f` bỏ qua .gitignore, dễ đưa data/checkpoint lên git. Hãy add từng file cần thiết.")
        out = git(["add", "--dry-run"] + args, cwd)            # đúng danh sách file lệnh này sẽ add
        to_be_added += re.findall(r"^add '(.*)'$", out, flags=re.M)

    if to_be_added or re.search(r"\bgit\s+commit\b", cmd):
        staged = git(["diff", "--cached", "--name-only"], cwd).splitlines() if re.search(r"\bgit\s+commit\b", cmd) else []
        bad = check_files(sorted(set(to_be_added + staged)), cwd)
        if bad:
            deny("Không được đưa lên git (CLAUDE.md, quy tắc 1): " + ", ".join(bad)
                 + ". Bỏ stage bằng `git restore --staged <file>` và thêm mẫu tương ứng vào .gitignore.")

    for seg in segments:
        if re.search(r"\b(cat|type|Get-Content|gc|more|less|head|tail)\b.*" + SECRET_FILES, seg) or \
           re.search(r"\b(echo|printenv|Write-Output|print)\b.*" + SECRET_VARS, seg):
            deny("Lệnh này in secret ra màn hình/log. Không đọc hay in token; "
                 "nếu cần kiểm tra token có tồn tại, dùng `test -n \"$HF_TOKEN\" && echo set`.")

    sys.exit(0)


if __name__ == "__main__":
    main()
