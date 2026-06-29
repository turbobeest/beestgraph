import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

const VAULT_PATH =
  process.env.VAULT_PATH ??
  path.join(process.env.HOME ?? "/home/turbobeest", "vault");

const REVIEW_STATUSES = new Set(["qualifying", "draft", "inbox", "actionable"]);

interface ReviewItem {
  title: string;
  path: string;
  folder: string;
  status: string;
  para?: string;
  content_stage?: string;
  topics?: string[];
  tags?: string[];
  summary?: string;
  type?: string;
  source_type?: string;
  modified: number;
  body: string;
  recommended_type?: string;
  recommended_topic?: string;
  recommended_tags?: string[];
  recommended_quality?: string;
  recommended_summary?: string;
}

// GET /api/review — list all files needing review
// GET /api/review?path=foo/bar.md — single file detail
export async function GET(request: NextRequest): Promise<NextResponse> {
  const singlePath = request.nextUrl.searchParams.get("path");

  if (singlePath) {
    const item = readSingleFile(singlePath);
    if (!item) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }
    return NextResponse.json(item);
  }

  const items: ReviewItem[] = [];
  scanForReview(VAULT_PATH, items, 0);
  items.sort((a, b) => b.modified - a.modified);
  return NextResponse.json({ items, total: items.length });
}

// PUT /api/review — approve (set status: published) or defer (add note)
export async function PUT(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json();
    const { path: filePath, action, note } = body as {
      path: string;
      action: "approve" | "defer";
      note?: string;
    };

    if (!filePath) {
      return NextResponse.json({ error: "path required" }, { status: 400 });
    }

    const fullPath = path.join(VAULT_PATH, filePath);
    if (!fullPath.startsWith(VAULT_PATH) || !fs.existsSync(fullPath)) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }

    let raw = fs.readFileSync(fullPath, "utf-8");
    const fmMatch = raw.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
    if (!fmMatch) {
      return NextResponse.json(
        { error: "No frontmatter found" },
        { status: 400 },
      );
    }

    let fmText = fmMatch[1]!;
    const bodyText = fmMatch[2] ?? "";

    if (action === "approve") {
      // Change status to published
      if (/^status:\s*.+$/m.test(fmText)) {
        fmText = fmText.replace(/^status:\s*.+$/m, "status: published");
      } else {
        fmText = fmText.trimEnd() + "\nstatus: published";
      }
    } else if (action === "defer" && note) {
      // Add/update review_note field
      if (/^review_note:\s*.+$/m.test(fmText)) {
        fmText = fmText.replace(
          /^review_note:\s*.+$/m,
          `review_note: "${note.replace(/"/g, '\\"')}"`,
        );
      } else {
        fmText =
          fmText.trimEnd() +
          `\nreview_note: "${note.replace(/"/g, '\\"')}"`;
      }
    }

    raw = `---\n${fmText}\n---\n${bodyText}`;
    fs.writeFileSync(fullPath, raw, "utf-8");

    return NextResponse.json({ success: true, action, path: filePath });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Failed to update review";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

function readSingleFile(filePath: string): ReviewItem | null {
  const fullPath = path.join(VAULT_PATH, filePath);
  if (!fullPath.startsWith(VAULT_PATH) || !fs.existsSync(fullPath)) {
    return null;
  }
  return parseFile(fullPath, filePath);
}

function parseFile(fullPath: string, relPath: string): ReviewItem | null {
  try {
    const content = fs.readFileSync(fullPath, "utf-8");
    const fmMatch = content.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
    if (!fmMatch) return null;

    const fmText = fmMatch[1]!;
    const body = fmMatch[2] ?? "";

    const get = (key: string): string | undefined => {
      const m = fmText.match(new RegExp(`^${key}:\\s*["']?(.+?)["']?\\s*$`, "m"));
      return m?.[1];
    };

    const getArray = (key: string): string[] => {
      const items: string[] = [];
      const block = fmText.match(
        new RegExp(`^${key}:\\s*\\n((?:(?!---)\\s*-\\s*.+\\n?)*)`, "m"),
      );
      if (block?.[1]) {
        for (const line of block[1].split("\n")) {
          const item = line.match(/^\s*-\s+(.+)/);
          if (item?.[1])
            items.push(item[1].replace(/^["']|["']$/g, "").trim());
        }
      }
      return items;
    };

    const stat = fs.statSync(fullPath);

    return {
      title: get("title") ?? path.basename(relPath, ".md"),
      path: relPath,
      folder: path.dirname(relPath),
      status: get("status") ?? "unknown",
      para: get("para"),
      content_stage: get("content_stage"),
      topics: getArray("topics"),
      tags: getArray("tags"),
      summary: get("summary"),
      type: get("type"),
      source_type: get("source_type"),
      modified: stat.mtimeMs,
      body,
      recommended_type: get("recommended_type"),
      recommended_topic: get("recommended_topic"),
      recommended_tags: getArray("recommended_tags"),
      recommended_quality: get("recommended_quality"),
      recommended_summary: get("recommended_summary"),
    };
  } catch {
    return null;
  }
}

function scanForReview(
  dir: string,
  results: ReviewItem[],
  depth: number,
): void {
  if (depth > 4) return;
  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.name.startsWith(".")) continue;
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (
          !["node_modules", "Templates", ".obsidian", ".trash"].includes(
            entry.name,
          )
        ) {
          scanForReview(full, results, depth + 1);
        }
      } else if (entry.name.endsWith(".md")) {
        // Quick status check before full parse
        const content = fs.readFileSync(full, "utf-8");
        const statusMatch = content.match(/^status:\s*["']?(.+?)["']?\s*$/m);
        const status = statusMatch?.[1];
        if (status && REVIEW_STATUSES.has(status)) {
          const rel = path.relative(VAULT_PATH, full);
          const item = parseFile(full, rel);
          if (item) results.push(item);
        }
      }
    }
  } catch {
    /* skip unreadable dirs */
  }
}
