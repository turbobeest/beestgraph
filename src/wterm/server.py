"""WebSocket → PTY bridge for the per-entry wiki terminal.

Spawns ``scripts/wiki-claude <entry>`` per WebSocket connection, then pumps
bytes between the PTY and the browser. Authentication is delegated to
Tailscale ACLs — bind to the interface Tailscale exposes.

Protocol (asymmetric, raw bytes by default):
    Client → Server  : binary frame of raw keystrokes for the PTY.
                       OR a frame whose first byte is 0x1F (Unit Separator)
                       followed by a UTF-8 JSON control message.
                       Supported control: ``{"type": "resize", "cols": N, "rows": M}``
    Server → Client  : binary frame of raw PTY output bytes (no framing).

The 0x1F sentinel is non-printable and is never produced by a keyboard, so
it cleanly separates control traffic from terminal input on a single channel.
"""

from __future__ import annotations

import asyncio
import errno
import fcntl
import json
import logging
import os
import pty
import signal
import struct
import sys
import termios
from pathlib import Path

from aiohttp import WSMsgType, web

logger = logging.getLogger("wterm")

VAULT = Path(os.environ.get("WTERM_VAULT", os.path.expanduser("~/vault"))).resolve()
SCRIPTS = Path("/home/turbobeest/beestgraph/scripts")
LAUNCHERS: dict[str, Path] = {
    "entry":  SCRIPTS / "wiki-claude",
    "audit":  SCRIPTS / "audit-claude",
    "review": SCRIPTS / "review-claude",
}
HOST = os.environ.get("WTERM_HOST", "0.0.0.0")
PORT = int(os.environ.get("WTERM_PORT", "3002"))

CTRL_PREFIX = 0x1F

# Audit recommendation IDs are hyphenated alphanumerics — strict allow-list.
import re as _re

_REC_ID_RE = _re.compile(r"^[A-Za-z0-9_\-]{1,128}$")


def _resolve_entry(rel_or_abs: str) -> Path | None:
    """Resolve a vault-relative or absolute path, refusing anything outside VAULT."""
    if not rel_or_abs:
        return None
    candidate = Path(rel_or_abs)
    if not candidate.is_absolute():
        candidate = VAULT / rel_or_abs
    try:
        resolved = candidate.resolve(strict=True)
    except (FileNotFoundError, RuntimeError):
        return None
    try:
        resolved.relative_to(VAULT)
    except ValueError:
        return None
    if not resolved.is_file():
        return None
    return resolved


def _validate_rec_id(rec_id: str) -> bool:
    return bool(_REC_ID_RE.match(rec_id))


def _resolve_launch_args(mode: str, target: str) -> list[str] | None:
    """Return [launcher_path, *argv] for the given mode/target, or None on bad input."""
    launcher = LAUNCHERS.get(mode)
    if launcher is None or not launcher.is_file():
        return None
    if mode in ("entry", "review"):
        path = _resolve_entry(target)
        if path is None:
            return None
        return [str(launcher), str(path)]
    if mode == "audit":
        if not _validate_rec_id(target):
            return None
        return [str(launcher), target]
    return None


def _set_winsize(fd: int, cols: int, rows: int) -> None:
    """Apply terminal window size to the PTY master fd."""
    cols = max(1, min(cols, 1000))
    rows = max(1, min(rows, 1000))
    winsz = struct.pack("HHHH", rows, cols, 0, 0)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsz)


async def wterm_handler(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(heartbeat=30, max_msg_size=1 << 20)
    await ws.prepare(request)

    # New protocol: ?mode=entry|audit|review&target=<path-or-id>
    # Backward-compat: ?entry=<path> still resolves to mode=entry.
    mode = request.query.get("mode", "entry")
    target = request.query.get("target") or request.query.get("entry", "")

    launch_argv = _resolve_launch_args(mode, target)
    if launch_argv is None:
        await ws.send_bytes(
            f"\r\n\x1b[31mInvalid request: mode={mode!r} target={target!r}\x1b[0m\r\n"
            f"Allowed modes: {sorted(LAUNCHERS)} | Vault root: {VAULT}\r\n".encode()
        )
        await ws.close()
        return ws

    cols = max(1, min(int(request.query.get("cols", "120")), 1000))
    rows = max(1, min(int(request.query.get("rows", "32")), 1000))

    logger.info(
        "wterm session opening: mode=%s target=%s cols=%d rows=%d",
        mode, target, cols, rows,
    )

    pid, fd = pty.fork()
    if pid == 0:
        # Child — exec the launcher.
        try:
            _set_winsize(0, cols, rows)
        except OSError:
            pass
        os.environ.setdefault("TERM", "xterm-256color")
        try:
            os.execvp(launch_argv[0], launch_argv)
        except OSError as e:
            sys.stderr.write(f"wterm: failed to exec launcher: {e}\n")
            os._exit(127)

    # Parent — pump bytes.
    _set_winsize(fd, cols, rows)
    loop = asyncio.get_running_loop()
    pty_done = asyncio.Event()

    def _on_pty_readable() -> None:
        try:
            data = os.read(fd, 65536)
        except OSError as e:
            if e.errno in (errno.EIO, errno.EBADF):
                pty_done.set()
                return
            raise
        if not data:
            pty_done.set()
            return
        asyncio.create_task(_safe_send(data))

    async def _safe_send(data: bytes) -> None:
        if ws.closed:
            return
        try:
            await ws.send_bytes(data)
        except (ConnectionResetError, RuntimeError):
            pty_done.set()

    loop.add_reader(fd, _on_pty_readable)

    async def _close_child() -> None:
        try:
            loop.remove_reader(fd)
        except (ValueError, OSError):
            pass
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        # Reap.
        for _ in range(20):
            try:
                done_pid, _ = os.waitpid(pid, os.WNOHANG)
                if done_pid == pid:
                    break
            except ChildProcessError:
                break
            await asyncio.sleep(0.1)
        else:
            try:
                os.kill(pid, signal.SIGKILL)
                os.waitpid(pid, 0)
            except (ProcessLookupError, ChildProcessError):
                pass
        try:
            os.close(fd)
        except OSError:
            pass

    async def _watch_pty_done() -> None:
        await pty_done.wait()
        if not ws.closed:
            await ws.close()

    watch_task = asyncio.create_task(_watch_pty_done())

    try:
        async for msg in ws:
            if msg.type == WSMsgType.BINARY:
                data = msg.data
            elif msg.type == WSMsgType.TEXT:
                data = msg.data.encode("utf-8")
            else:
                continue
            if not data:
                continue
            if data[0] == CTRL_PREFIX:
                try:
                    ctl = json.loads(data[1:].decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                if ctl.get("type") == "resize":
                    try:
                        _set_winsize(fd, int(ctl.get("cols", cols)), int(ctl.get("rows", rows)))
                    except (OSError, ValueError, TypeError):
                        pass
                continue
            try:
                os.write(fd, data)
            except OSError:
                break
    finally:
        watch_task.cancel()
        await _close_child()
        logger.info("wterm session closed: mode=%s target=%s", mode, target)

    return ws


async def healthz(_request: web.Request) -> web.Response:
    return web.Response(text="ok\n")


def make_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/wterm", wterm_handler)
    app.router.add_get("/healthz", healthz)
    return app


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("WTERM_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    logger.info("wterm listening on %s:%d, vault=%s, launchers=%s", HOST, PORT, VAULT, sorted(LAUNCHERS))
    web.run_app(make_app(), host=HOST, port=PORT, print=None)


if __name__ == "__main__":
    main()
