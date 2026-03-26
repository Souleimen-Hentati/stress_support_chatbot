import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "server"))

from server.main import app

__all__ = ["app"]

