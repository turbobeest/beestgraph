#!/usr/bin/env python3
"""Migrate vault directory structure to numbered lifecycle layout.

Moves files from the old flat layout to the new numbered directories::

    inbox/      -> 01-inbox/
    queue/      -> 02-queue/
    daily/      -> 04-daily/
    projects/   -> 05-projects/
    areas/      -> 06-areas/
    knowledge/  -> 07-resources/   (preserves subdirectory tree)
    archives/   -> 08-archive/
    templates/  -> 00-meta/templates/

After moving, old empty directories are removed.

Usage::

    python scripts/migrate-vault-structure.py [--vault-path ~/vault] [--dry-run]
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


# (old_dir, new_dir)
_MIGRATIONS: list[tuple[str, str]] = [
    ("inbox", "01-inbox"),
    ("queue", "02-queue"),
    ("daily", "04-daily"),
    ("projects", "05-projects"),
    ("areas", "06-areas"),
    ("knowledge", "07-resources"),
    ("archives", "08-archive"),
    ("templates", "00-meta/templates"),
]

# Extra directories to create (even if no files to move)
_NEW_DIRS: list[str] = [
    "00-meta",
    "00-meta/templates",
    "00-meta/mocs",
    "00-meta/dashboards",
    "00-meta/settings",
    "01-inbox",
    "02-queue",
    "02-queue/.notifications",
    "03-fleeting",
    "04-daily",
    "05-projects",
    "06-areas",
    "07-resources",
    "08-archive",
    "08-archive/projects",
    "08-archive/rejected",
    "09-attachments",
]


def _move_contents(src: Path, dst: Path, dry_run: bool = False) -> int:
    """Move all files and directories from *src* into *dst*.

    Args:
        src: Source directory.
        dst: Destination directory (created if needed).
        dry_run: If True, only print what would happen.

    Returns:
        Number of items moved.
    """
    if not src.is_dir():
        return 0

    dst.mkdir(parents=True, exist_ok=True)
    count = 0

    for item in sorted(src.iterdir()):
        # Skip hidden dirs like .obsidian
        if item.name.startswith("."):
            continue
        target = dst / item.name
        if dry_run:
            print(f"  [DRY RUN] {item} -> {target}")
        else:
            if target.exists() and item.is_dir():
                # Merge directory contents recursively
                count += _move_contents(item, target, dry_run)
                continue
            shutil.move(str(item), str(target))
            print(f"  Moved: {item.name}")
        count += 1

    return count


def _remove_empty_dirs(vault: Path, names: list[str], dry_run: bool = False) -> None:
    """Remove old directories if they are empty.

    Args:
        vault: Vault root path.
        names: Directory names to check.
        dry_run: If True, only print what would happen.
    """
    for name in names:
        d = vault / name
        if d.is_dir() and not any(d.iterdir()):
            if dry_run:
                print(f"  [DRY RUN] Would remove empty: {d}")
            else:
                d.rmdir()
                print(f"  Removed empty: {d}")


def _migrate_notifications(vault: Path, dry_run: bool = False) -> None:
    """Move .notifications/ from vault root to 02-queue/.notifications/.

    Args:
        vault: Vault root path.
        dry_run: If True, only print what would happen.
    """
    old_notif = vault / ".notifications"
    new_notif = vault / "02-queue" / ".notifications"
    if old_notif.is_dir():
        new_notif.mkdir(parents=True, exist_ok=True)
        _move_contents(old_notif, new_notif, dry_run)
        if not dry_run and not any(old_notif.iterdir()):
            old_notif.rmdir()
            print(f"  Removed empty: {old_notif}")


def main() -> None:
    """Run the vault migration."""
    parser = argparse.ArgumentParser(description="Migrate vault to numbered layout")
    parser.add_argument(
        "--vault-path",
        type=Path,
        default=Path.home() / "vault",
        help="Path to the vault root (default: ~/vault)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without making changes",
    )
    args = parser.parse_args()
    vault: Path = args.vault_path.expanduser().resolve()
    dry_run: bool = args.dry_run

    if not vault.is_dir():
        print(f"Vault not found: {vault}")
        return

    print(f"Migrating vault: {vault}")
    if dry_run:
        print("(DRY RUN — no changes will be made)\n")

    # 1. Create all new directories
    print("\n=== Creating new directories ===")
    for d in _NEW_DIRS:
        target = vault / d
        if not target.exists():
            if dry_run:
                print(f"  [DRY RUN] mkdir {target}")
            else:
                target.mkdir(parents=True, exist_ok=True)
                print(f"  Created: {target}")

    # 2. Move files from old -> new
    print("\n=== Moving files ===")
    total_moved = 0
    for old_name, new_name in _MIGRATIONS:
        old_dir = vault / old_name
        new_dir = vault / new_name
        if old_dir.is_dir() and old_dir != new_dir:
            print(f"\n  {old_name}/ -> {new_name}/")
            count = _move_contents(old_dir, new_dir, dry_run)
            total_moved += count
            if count == 0:
                print(f"    (empty or already migrated)")

    # 3. Move .notifications/ to 02-queue/.notifications/
    print("\n=== Moving notifications ===")
    _migrate_notifications(vault, dry_run)

    # 4. Remove old empty directories
    print("\n=== Cleaning up empty directories ===")
    old_names = [old for old, _new in _MIGRATIONS]
    _remove_empty_dirs(vault, old_names, dry_run)

    print(f"\nMigration complete. {total_moved} items moved.")


if __name__ == "__main__":
    main()
