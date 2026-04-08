import { NextRequest, NextResponse } from "next/server";

import fs from "fs";
import path from "path";

const VAULT_PATH = process.env.VAULT_PATH ?? path.join(process.env.HOME ?? "/home/turbobeest", "vault");

// GET /api/wiki?path=Eat-Drink-Merriment/Recipes - Meals.md
// Returns { frontmatter, body, wikilinks, backlinks }
export async function GET(request: NextRequest): Promise<NextResponse> {
  const filePath = request.nextUrl.searchParams.get("path") ?? "";

  if (!filePath) {
    // List all wiki pages
    return listPages();
  }

  const fullPath = path.join(VAULT_PATH, filePath);

  // Security: prevent path traversal
  if (!fullPath.startsWith(VAULT_PATH)) {
    return NextResponse.json({ error: "Invalid path" }, { status: 400 });
  }

  if (!fs.existsSync(fullPath)) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  const raw = fs.readFileSync(fullPath, "utf-8");

  // Parse frontmatter
  const fmMatch = raw.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  let frontmatter: Record<string, unknown> = {};
  let body = raw;
  if (fmMatch) {
    try {
      // Simple YAML parse for display (key: value lines)
      const fmLines = fmMatch[1]!.split("\n");
      const fm: Record<string, unknown> = {};
      for (const line of fmLines) {
        const match = line.match(/^(\w[\w\s-]*?):\s*(.*)$/);
        if (match && !line.startsWith("  ") && !line.startsWith("#")) {
          let val: unknown = match[2]!.replace(/^["']|["']$/g, "");
          if (val === "true") val = true;
          else if (val === "false") val = false;
          else if (!isNaN(Number(val)) && val !== "") val = Number(val);
          fm[match[1]!.trim()] = val;
        }
      }
      frontmatter = fm;
    } catch { /* ignore parse errors */ }
    body = fmMatch[2] ?? "";
  }

  // Extract wikilinks from body
  const wikilinks: string[] = [];
  const wlRegex = /\[\[([^\]|]+)(?:\|[^\]]+)?\]\]/g;
  let wlMatch;
  while ((wlMatch = wlRegex.exec(body)) !== null) {
    if (wlMatch[1] && !wikilinks.includes(wlMatch[1])) {
      wikilinks.push(wlMatch[1]);
    }
  }

  // Find backlinks (other files that link to this page)
  const backlinks: Array<{ title: string; path: string }> = [];
  const pageTitle = String(frontmatter.title ?? path.basename(filePath, ".md"));
  const pageStem = path.basename(filePath, ".md");

  findBacklinks(VAULT_PATH, pageTitle, pageStem, backlinks, VAULT_PATH);

  return NextResponse.json({
    path: filePath,
    frontmatter,
    body,
    wikilinks,
    backlinks,
  });
}

function findBacklinks(
  dir: string,
  title: string,
  stem: string,
  results: Array<{ title: string; path: string }>,
  vaultRoot: string,
  depth = 0,
) {
  if (depth > 5) return; // Don't go too deep
  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.name.startsWith(".")) continue;
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (!["node_modules", "Templates", ".obsidian", ".trash"].includes(entry.name)) {
          findBacklinks(full, title, stem, results, vaultRoot, depth + 1);
        }
      } else if (entry.name.endsWith(".md") && results.length < 30) {
        const content = fs.readFileSync(full, "utf-8");
        if (content.includes(`[[${title}]]`) || content.includes(`[[${stem}]]`) ||
            content.includes(`[[${title}|`) || content.includes(`[[${stem}|`)) {
          const rel = path.relative(vaultRoot, full);
          // Extract title from frontmatter
          const titleMatch = content.match(/^title:\s*["']?(.+?)["']?\s*$/m);
          results.push({
            title: titleMatch?.[1] ?? path.basename(full, ".md"),
            path: rel,
          });
        }
      }
    }
  } catch { /* skip unreadable dirs */ }
}

function listPages(): NextResponse {
  const pages: Array<{ title: string; path: string; folder: string }> = [];

  function scan(dir: string, depth = 0) {
    if (depth > 4) return;
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.name.startsWith(".")) continue;
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          if (!["node_modules", "Templates", ".obsidian", ".trash"].includes(entry.name)) {
            scan(full, depth + 1);
          }
        } else if (entry.name.endsWith(".md")) {
          const rel = path.relative(VAULT_PATH, full);
          const content = fs.readFileSync(full, "utf-8");
          const titleMatch = content.match(/^title:\s*["']?(.+?)["']?\s*$/m);
          pages.push({
            title: titleMatch?.[1] ?? path.basename(full, ".md"),
            path: rel,
            folder: path.dirname(rel),
          });
        }
      }
    } catch { /* skip */ }
  }

  scan(VAULT_PATH);
  pages.sort((a, b) => a.folder.localeCompare(b.folder) || a.title.localeCompare(b.title));
  return NextResponse.json({ pages });
}

// POST /api/wiki — save edits to a vault file
export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const { path: filePath, content } = await request.json();

    if (!filePath || typeof content !== "string") {
      return NextResponse.json({ error: "path and content required" }, { status: 400 });
    }

    const fullPath = path.join(VAULT_PATH, filePath);
    if (!fullPath.startsWith(VAULT_PATH)) {
      return NextResponse.json({ error: "Invalid path" }, { status: 400 });
    }

    // Ensure directory exists
    fs.mkdirSync(path.dirname(fullPath), { recursive: true });
    fs.writeFileSync(fullPath, content, "utf-8");

    return NextResponse.json({ success: true, path: filePath });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Save failed";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
