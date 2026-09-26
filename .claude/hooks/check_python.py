"""PostToolUse hook (Edit | Write): kiểm tra cú pháp file .py ngay sau khi Claude sửa.

PostToolUse không chặn được (file đã được ghi), nên hook trả về additionalContext:
Claude nhận thông báo lỗi và sửa ngay ở bước tiếp theo, thay vì phát hiện muộn khi chạy test.
Kiểm tra bằng Python của .venv (cùng phiên bản với code), không có thì dùng Python đang chạy hook.

Test tay (Git Bash):
  echo '{"tool_name":"Edit","tool_input":{"file_path":"src/model.py"}}' | python .claude/hooks/check_python.py
"""
import json
import os
import subprocess
import sys

CHECK = "import ast, sys; ast.parse(open(sys.argv[1], encoding='utf-8').read(), sys.argv[1])"


def main():
    data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    path = data.get("tool_input", {}).get("file_path", "")
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    full = os.path.join(root, path)
    if not path.endswith(".py") or not os.path.isfile(full):
        sys.exit(0)

    python = sys.executable
    for candidate in (os.path.join(root, ".venv", "Scripts", "python.exe"), os.path.join(root, ".venv", "bin", "python")):
        if os.path.isfile(candidate):
            python = candidate
            break

    r = subprocess.run([python, "-c", CHECK, full], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        err = (r.stderr or r.stdout).strip()[-1500:]
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "Lỗi cú pháp sau khi sửa %s:\n%s\nSửa lỗi này trước khi làm tiếp." % (path, err),
            },
            "systemMessage": "Hook check_python: lỗi cú pháp trong %s" % path,
        }))
    sys.exit(0)


if __name__ == "__main__":
    main()
