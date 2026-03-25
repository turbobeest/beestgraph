"""Allow running the heartbeat daemon as ``python -m src.heartbeat.daemon``."""

from __future__ import annotations

from src.heartbeat.daemon import main

if __name__ == "__main__":
    main()
