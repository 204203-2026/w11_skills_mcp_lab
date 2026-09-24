"""Offline pytest entry point; pytest's no-tests status remains a failure."""
import os
import sys
from pathlib import Path

os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest

raise SystemExit(pytest.main(["-q", *sys.argv[1:]]))
