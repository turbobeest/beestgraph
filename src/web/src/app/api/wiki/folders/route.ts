import { NextResponse } from "next/server";

import fs from "fs";
import path from "path";

const VAULT_PATH = process.env.VAULT_PATH ?? path.join(process.env.HOME ?? "/home/turbobeest", "vault");

// GET /api/wiki/folders — returns all vault folders as a flat list
export async function GET(): Promise<NextResponse> {
  const folders: string[] = [];

  function scan(dir: string, depth = 0) {
    if (depth > 4) return;
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        if (!entry.isDirectory() || entry.name.startsWith(".")) continue;
        if (["node_modules", "Templates", ".obsidian", ".trash"].includes(entry.name)) continue;
        const rel = path.relative(VAULT_PATH, path.join(dir, entry.name));
        folders.push(rel);
        scan(path.join(dir, entry.name), depth + 1);
      }
    } catch { /* skip */ }
  }

  scan(VAULT_PATH);
  folders.sort();
  return NextResponse.json({ folders });
}
