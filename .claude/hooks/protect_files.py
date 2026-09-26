"""PreToolUse hook (Edit | Write | NotebookEdit): bảo vệ file nhạy cảm và file được sinh tự động.

- deny: secret (.env, kaggle.json, *.pem), .git/, data/checkpoint, notebook .ipynb (sinh từ scripts/make_notebooks.py)
- ask : .claude/settings.json và .claude/hooks/* (Claude tự sửa "harness" của chính nó → người phải duyệt)

Test tay (Git Bash):
  echo '{"tool_name":"Write","tool_input":{"file_path":".env"}}' | python .claude/hooks/protect_files.py
"""
import json
import os
import re
import sys

DENY = [
    (r"(^|/)\.env(\..*)?$|(^|/)kaggle\.json$|\.pem$", "file chứa secret, không để Claude đọc/ghi"),
    (r"^\.git/", "thư mục nội bộ của git"),
    (r"^(data|checkpoints|ckpt|outputs)/", "dữ liệu/checkpoint do script sinh ra, không sửa tay"),
    (r"^notebooks/.*\.ipynb$", "notebook được sinh từ scripts/make_notebooks.py: sửa file đó rồi chạy "
                               "`python scripts/make_notebooks.py`"),
]
ASK = [
    (r"^\.claude/(settings\.json|hooks/)", "Claude đang sửa harness (settings/hooks) của chính nó, cần người duyệt"),
]


def decide(decision, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def main():
    data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    tool_input = data.get("tool_input", {})
    path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    try:
        rel = os.path.relpath(os.path.join(root, path), root)
    except ValueError:                       # Windows: khác ổ đĩa
        rel = path
    rel = rel.replace("\\", "/")

    for pattern, reason in DENY:
        if re.search(pattern, rel):
            decide("deny", "Không sửa `%s`: %s." % (rel, reason))
    for pattern, reason in ASK:
        if re.search(pattern, rel):
            decide("ask", reason)
    sys.exit(0)


if __name__ == "__main__":
    main()
