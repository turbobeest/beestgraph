# beestgraph — Session Resume

**Codeword:** `bzzz` (user types this; agent reads this file in full and continues).

> Last updated: 2026-05-03 by Claude Opus 4.7 (1M).
> If you are a fresh Claude Code session and the user said `bzzz` (or referenced this file),
> read this whole doc, then **pick up at the "Resume action" section at the bottom**.

---

## What was built in this session

### 1. Headless mode hardening (done)
- Disabled GUI services and purged ~50 packages from the desktop image
  (piwiz, pi-package*, rpi-imager, piclone, lxterminal, lxtask, rpd-wallpaper-trixie,
  cups, bluez, sane-utils, firmware-atheros, firmware-mediatek, etc.)
- Disabled services: `wayvnc-control`, `NetworkManager-wait-online`, `sshswitch`,
  `regenerate_ssh_host_keys`, `avahi-daemon`, `bluetooth`, `cups*`,
  cloud-init-* (masked).
- **Re-enabled later**: `rpcbind`, `rpcbind.socket`, `rpc-statd` — needed by NFS
  for the `walnut-drive` mount.
- Boot time: ~14.5s → faster after kernel cleanup.

### 2. PWA + mobile-friendly responsive UI (done)
- Generated icons from `~/beestgraph/beestgraph.jpg`: `icon-{192,512}.png`,
  `apple-touch-icon.png`.
- Added `manifest.json` and apple-mobile-web-app meta tags to all surfaces.
- `@media (max-width: 768px)` blocks added to `wiki.html`, `audit.html`,
  `review.html`. Wiki gets a hamburger drawer for the sidebar.
- Next.js `Sidebar.tsx` made horizontally-scrollable on small screens.
- 3D graph and dashboard intentionally **not** mobile-targeted.

### 3. Audit page UX (done)
- Per-entry **Delete** button (red, with confirm) on pending/deferred cards.
- **Clear all approved** bulk button next to filters.
- Backend `DELETE /api/audit` extended to accept `{status: "approved"}` for bulk.

### 4. Talk-to-Claude per-entry terminals (the big one — done)
**Architecture:**
```
Browser ─── HTTP/WS ───► Caddy (:80) ──┬─► Next.js (:3001)   wiki/audit/queue/...
                                       └─► wterm    (:3002)  /wterm WebSocket
                                                │
                                                └─► PTY ──► launcher ──► claude
                                                                          (Opus 4.7
                                                                           + wiki-curator skill
                                                                           + --dangerously-skip-permissions)
```

**Files added:**
- `~/beestgraph/.claude/skills/wiki-curator/SKILL.md` — codifies the curation
  rubric (PARA / ZETT / TREE / ATLAS / GRAPH dimensions, frontmatter spec,
  interlink discipline). Project-scoped, auto-discovered.
- `~/beestgraph/scripts/wiki-claude` — vault entry launcher.
- `~/beestgraph/scripts/audit-claude` — audit recommendation launcher.
  Reads from `config/audit-recommendations.json`.
- `~/beestgraph/scripts/review-claude` — review-queue entry launcher.
- `~/beestgraph/src/wterm/{__init__,server}.py` — aiohttp WebSocket↔PTY bridge.
  Dispatches by `?mode=entry|audit|review&target=...`.
  Resize control via `0x1F`-prefixed JSON frames.
- `~/beestgraph/config/systemd/beestgraph-wterm.service` (installed; active).
- `~/beestgraph/src/web/public/talk-to-claude.{css,js}` — shared floating panel
  widget. Used by all three pages. Lazy-loads `@wterm/dom@0.3.0` and
  `@wterm/ghostty@0.3.0` from esm.sh on first open.
- `/etc/caddy/Caddyfile` — reverse-proxy `/wterm` + `/healthz/wterm` → 3002.

**Behaviour:**
- Floating panel (resizable, draggable, has `⛶` maximize toggle).
- Each launcher's system prompt instructs Claude to:
  1. Read the file.
  2. Write a 4-7 sentence specific assessment paragraph.
  3. Ask 2-4 focused questions.
  4. Wait for user direction before editing.
- Auto-kickoff: launcher passes positional prompt to claude so the assessment
  fires immediately on connection (no user "go" needed). Override via
  `KICKOFF=...` env var.
- All three use `--dangerously-skip-permissions` (per user request) bounded by
  `--add-dir $VAULT` + project cwd.

**Security posture:** wterm binds 127.0.0.1 only; reachable solely via Caddy
on :80. Tailscale gates the tailnet. Path-traversal in audit IDs rejected
(strict alphanumeric/hyphen allow-list).

**Styling notes:**
- Built-in wterm cursor was rendering as light-gray (`#aeafad`) block,
  reading as a "white bar" on Claude Code's input row.
- Current overrides in `talk-to-claude.css`:
  `--term-fg: #6b7785` (muted slate so reverse-video bg isn't bright),
  `--term-cursor: #60a5fa` (soft blue),
  `cursorBlink: false` in JS to reduce flicker.
- This was originally going to be tightened against a "dashboard-design"
  reference, but the user clarified that reference belonged to a different
  project ("switch"), not beestgraph. No further design-token alignment
  pursued here.

---

## Open work (deferred, not blocking)

### A. Comprehensive `bg` CLI (for the future personal-assistant agent)
The user wants their assistant agent to have full beestgraph autonomy via CLI.
Existing `bg` covers: `daily, task, find, project, health, context, init,
capture, save, export, archive, ingest, recap, review, migrate, think`.
**Gaps to fill:**
- `bg audit {list,approve,defer,delete,execute,clear-approved}` — audit loop.
- `bg wiki {view,edit,backlinks,links}` — entry-level read/write by path.
- `bg queue {list,get,classify,promote}` — inbox triage.
- `bg curate <entry>` — non-interactive wrapper around the wiki-curator skill
  (the wiki-claude launcher in `--print` JSON mode).

### B. Personal assistant agent itself
Once the CLI gaps are filled. Outside scope of this session.

---

## Pending action items (post-reboot)

The user is about to reconfigure networking, then update NAS NFS ACL.

### Network change (user is doing this, NOT us)
- Switch `eth0` to static `192.168.1.12`.
- Disable `wlan0` entirely (currently `192.168.1.12`).
- After change: Pi reachable at `192.168.1.12` (wired), `100.74.63.55` (Tailscale).

### NAS NFS access (user is doing this — secondary, not blocking)
- The mount `192.168.2.2:/volume1/walnut-drive` → `/mnt/walnut-drive` is failing
  with "access denied by server" (server-side ACL).
- User is updating the NAS export ACL to allow the Pi's wired IP.
- Once mount works, screenshots and other shared assets become reachable
  again. NOT blocking any beestgraph work — the share's `dev/walnut-LAN/`
  contents belong to a separate project ("switch").

---

## Resume action (for the next Claude session)

When the user says `bzzz` (or asks to resume):

1. **Read** this file in full (you already did if you got here).
2. **Verify state** quickly:
   ```bash
   systemctl is-active beestgraph-wterm beestgraph-web caddy
   ip -4 addr show eth0 | grep inet              # expect 192.168.1.12
   nmcli radio wifi                              # expect "disabled"
   mountpoint /mnt/walnut-drive                   # may or may not be mounted; not blocking
   ```
3. **Network sanity:**
   - eth0 should be static `192.168.1.12`. If it shows `.242` or DHCP, the
     pre-shutdown switch didn't stick — re-run the network change in
     section "Pending action items" above.
   - `wlan0` should be down (radio off).
4. **Walnut-drive mount:** if `mountpoint /mnt/walnut-drive` says "is not a
   mountpoint", ask the user whether the NAS ACL fix went through. If yes,
   `sudo mount /mnt/walnut-drive`. If still failing, that's NOT blocking
   beestgraph work — move on.
5. **Resume the next feature.** The Talk-to-Claude work is shipped and
   styling is finalized for now. The next-up beestgraph task is the
   comprehensive `bg` CLI subcommands (section A above): `bg audit`,
   `bg wiki`, `bg queue`, `bg curate`. Ask the user which to start with;
   each is ~30-60 min and unlocks personal-assistant-agent autonomy.

---

## Key paths cheat-sheet

| Thing | Path |
|---|---|
| Project root | `~/beestgraph/` |
| Vault | `~/vault/` |
| Audit JSON | `~/beestgraph/config/audit-recommendations.json` |
| wterm service | `/etc/systemd/system/beestgraph-wterm.service` |
| wterm source | `~/beestgraph/src/wterm/server.py` |
| Caddyfile | `/etc/caddy/Caddyfile` |
| Skills dir | `~/beestgraph/.claude/skills/` |
| Web UI public | `~/beestgraph/src/web/public/` |
| Launchers | `~/beestgraph/scripts/{wiki,audit,review}-claude` |
| This doc | `~/beestgraph/docs/RESUME.md` |

## Quick health checks

```bash
# All services up
systemctl is-active beestgraph-{wterm,web,bot,heartbeat,obsidian-sync,vault-sync,watcher} caddy tailscaled docker

# wterm alive
curl -s http://localhost/healthz/wterm    # → "ok"

# wterm reachable through Caddy
curl -s -o /dev/null -w '%{http_code}\n' http://localhost/wiki.html

# Recent wterm logs
journalctl -u beestgraph-wterm --since "1 hour ago" --no-pager

# Last build of Next.js
ls -la ~/beestgraph/src/web/.next/build-manifest.json
```
