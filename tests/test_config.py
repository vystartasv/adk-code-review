"""Tests for the auto-inject config module."""
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


class TestConfig:
    """Tests for utilities/config.py auto-injection."""

    def test_import_does_not_crash(self):
        """Importing config should never crash, even without credential proxy."""
        import utilities.config  # noqa: F811
        # If we got here without exception, it worked

    def test_api_key_set_after_import(self):
        """After importing config, GOOGLE_API_KEY should be in environment."""
        import subprocess
        result = subprocess.run(
            ["python3.11", "-c",
             "import os; "
             "os.environ.pop('GOOGLE_API_KEY', None); "
             "import sys; sys.path.insert(0, '.'); "
             "import utilities.config; "
             "key = os.environ.get('GOOGLE_API_KEY', ''); "
             "assert len(key) > 10, f'Key missing or too short: {len(key)} chars'; "
             "print('OK')"],
            capture_output=True, text=True,
            cwd=str(project_root),
            timeout=10,
        )
        assert result.returncode == 0, f"Stderr: {result.stderr}"
