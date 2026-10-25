"""check.py: the one-command check (tests + text lint). The pre-commit hook runs this; exit code gates the commit."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

steps = [[sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-m", "not slow", str(ROOT / "tests")]]
lint = ROOT / "tools" / "lint.py"
if lint.exists():
    steps.append([sys.executable, "-X", "utf8", str(lint)])

for cmd in steps:
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode:
        sys.exit(f"check failed: {' '.join(cmd[3:])}")
print("check ok")
