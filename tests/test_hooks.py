"""Test các hook trong .claude/hooks/ bằng cách gửi JSON giống Claude Code qua stdin."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / ".claude" / "hooks"


def run_hook(name, payload, cwd=ROOT):
    r = subprocess.run([sys.executable, str(HOOKS / name)], input=json.dumps(payload).encode("utf-8"),
                       capture_output=True, cwd=cwd, timeout=60, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(cwd)))
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    out = r.stdout.decode("utf-8").strip()
    return json.loads(out) if out.startswith("{") else out


def decision(result):
    return result["hookSpecificOutput"]["permissionDecision"] if isinstance(result, dict) else None


def bash(cmd):
    return {"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": str(ROOT)}


def test_guard_blocks_force_push_anywhere_in_command():
    for cmd in ["git push -f", "git push origin main --force", "git push origin +main", "git push --force-with-lease"]:
        assert decision(run_hook("guard_bash.py", bash(cmd))) == "deny", cmd


def test_guard_allows_normal_commands():
    for cmd in ["git push origin main", "git push -u origin feature-fix", "git status", "python -m pytest -q"]:
        assert decision(run_hook("guard_bash.py", bash(cmd))) is None, cmd


def test_guard_blocks_forced_add_and_secret_printing():
    assert decision(run_hook("guard_bash.py", bash("git add -f checkpoints/x.pt"))) == "deny"
    assert decision(run_hook("guard_bash.py", bash("cat .env"))) == "deny"
    assert decision(run_hook("guard_bash.py", bash("echo $HF_TOKEN"))) == "deny"


def test_guard_blocks_committing_checkpoint(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "model.pt").write_bytes(b"x")
    payload = {"tool_name": "Bash", "tool_input": {"command": "git add model.pt && git commit -m x"}, "cwd": str(tmp_path)}
    result = run_hook("guard_bash.py", payload, cwd=tmp_path)
    assert decision(result) == "deny" and "model.pt" in result["hookSpecificOutput"]["permissionDecisionReason"]


def test_protect_files():
    def write(path):
        return run_hook("protect_files.py", {"tool_name": "Write", "tool_input": {"file_path": path}, "cwd": str(ROOT)})
    assert decision(write(".env")) == "deny"
    assert decision(write("notebooks/colab_train.ipynb")) == "deny"
    assert decision(write(".claude/settings.json")) == "ask"
    assert decision(write("src/model.py")) is None


def test_check_python_reports_syntax_error(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("def f(:\n    pass\n", encoding="utf-8")
    payload = {"tool_name": "Edit", "tool_input": {"file_path": str(bad)}, "cwd": str(tmp_path)}
    result = run_hook("check_python.py", payload, cwd=tmp_path)
    assert "Lỗi cú pháp" in result["hookSpecificOutput"]["additionalContext"]
    good = tmp_path / "good.py"
    good.write_text("x = 1\n", encoding="utf-8")
    assert run_hook("check_python.py", {"tool_name": "Edit", "tool_input": {"file_path": str(good)}}, cwd=tmp_path) == ""


def test_session_context_prints_plain_text():
    out = run_hook("session_context.py", {"source": "startup", "cwd": str(ROOT)})
    assert out.startswith("# Bối cảnh project")
