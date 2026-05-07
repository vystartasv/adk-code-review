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
        # Reload to test fresh
        import importlib
        if "utilities.config" in sys.modules:
            del sys.modules["utilities.config"]

        was_set = "GOOGLE_API_KEY" in os.environ
        saved = os.environ.get("GOOGLE_API_KEY")

        # Remove key to test auto-inject
        if "GOOGLE_API_KEY" in os.environ:
            del os.environ["GOOGLE_API_KEY"]

        try:
            import utilities.config  # noqa
            assert "GOOGLE_API_KEY" in os.environ
            assert len(os.environ["GOOGLE_API_KEY"]) > 10
        finally:
            # Restore
            if was_set and saved:
                os.environ["GOOGLE_API_KEY"] = saved
