import subprocess
import sys

from cs_types_ideas import __version__


def test_cli_version():
    cmd = [sys.executable, "-m", "cs_types_ideas", "--version"]
    assert subprocess.check_output(cmd).decode().strip() == __version__
