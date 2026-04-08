import { NextRequest, NextResponse } from "next/server";

import fs from "fs";
import path from "path";

const VAULT_PATH = process.env.VAULT_PATH ?? path.join(process.env.HOME ?? "/home/turbobeest", "vault");

// GET /api/wiki/suggest?q=docker — returns pages matching query for [[wikilink]] autocomplete
export async function GET(request: NextRequest): Promise<NextResponse> {
  const q = (request.nextUrl.searchParams.get("q") ?? "").toLowerCase();
  if (q.length < 1) return NextResponse.json({ suggestions: [] });

  const suggestions: Array<{ title: string; path: string }> = [];

  function scan(dir: string, depth = 0) {
    if (depth > 4 || suggestions.length >= 20) return;
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.name.startsWith(".") || suggestions.length >= 20) continue;
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          if (!["node_modules", "Templates", ".obsidian", ".trash"].includes(entry.name)) {
            scan(full, depth + 1);
          }
        } else if (entry.name.endsWith(".md")) {
          const stem = path.basename(entry.name, ".md").toLowerCase();
          if (stem.includes(q)) {
            const rel = path.relative(VAULT_PATH, full);
            const content = fs.readFileSync(full, "utf-8");
            const titleMatch = content.match(/^title:\s*["']?(.+?)["']?\s*$/m);
            suggestions.push({
              title: titleMatch?.[1] ?? path.basename(full, ".md"),
              path: rel,
            });
          }
        }
      }
    } catch { /* skip */ }
  }

  scan(VAULT_PATH);
  return NextResponse.json({ suggestions });
}
