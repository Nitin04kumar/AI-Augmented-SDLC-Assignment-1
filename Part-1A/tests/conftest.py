import json

import pytest

from todo.cli import main


@pytest.fixture
def data_file(tmp_path):
    return tmp_path / "tasks.json"


@pytest.fixture
def cli(data_file, capsys):
    """Run the CLI in-process. Returns (exit_code, stdout_json, stderr_json)."""

    def run(*args):
        code = main(["--data", str(data_file), *args])
        captured = capsys.readouterr()
        out = json.loads(captured.out) if captured.out.strip() else None
        err = json.loads(captured.err) if captured.err.strip() else None
        return code, out, err

    return run
