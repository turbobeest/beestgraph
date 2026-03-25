import { readdir, readFile, writeFile, mkdir, unlink } from "node:fs/promises";
import { join } from "node:path";

import { NextRequest, NextResponse } from "next/server";

import { slugFromFilename } from "@/lib/queue";

const VAULT_PATH = process.env.VAULT_PATH ?? join(process.env.HOME ?? "/root", "vault");
const QUEUE_DIR = process.env.QUEUE_DIR ?? "02-queue";
const ARCHIVE_DIR = process.env.ARCHIVE_DIR ?? "08-archive";

// ---------------------------------------------------------------------------
// Frontmatter helpers
// ---------------------------------------------------------------------------

interface Frontmatter {
  [key: string]: unknown;
}

function parseFrontmatter(raw: string): { data: Frontmatter; content: string } {
  if (!raw.startsWith("---")) return { data: {}, content: raw };
  const end = raw.indexOf("---", 3);
  if (end === -1) return { data: {}, content: raw };
  const yamlBlock = raw.slice(3, end).trim();
  const content = raw.slice(end + 3).trim();

  const data: Frontmatter = {};
  let currentKey = "";
  let currentList: string[] | null = null;

  for (const line of yamlBlock.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    if (trimmed.startsWith("- ") && currentList !== null) {
      let val = trimmed.slice(2).trim();
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) val = val.slice(1, -1);
      currentList.push(val);
      continue;
    }
    const colonIdx = trimmed.indexOf(":");
    if (colonIdx > 0) {
      if (currentList !== null && currentKey) data[currentKey] = currentList;
      currentList = null;
      const key = trimmed.slice(0, colonIdx).trim();
      let val = trimmed.slice(colonIdx + 1).trim();
      currentKey = key;
      if (val === "" || val === "[]") {
        data[key] = val === "[]" ? [] : undefined;
        if (val !== "[]") currentList = [];
        continue;
      }
      if (val.startsWith("[") && val.endsWith("]")) {
        const inner = val.slice(1, -1);
        data[key] = inner
          ? inner.split(",").map((s) => {
              let v = s.trim();
              if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) v = v.slice(1, -1);
              return v;
            })
          : [];
        continue;
      }
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) val = val.slice(1, -1);
      data[key] = val;
    }
  }
  if (currentList !== null && currentKey) data[currentKey] = currentList;
  return { data, content };
}

function serializeFrontmatter(data: Frontmatter): string {
  const lines: string[] = [];
  for (const [key, value] of Object.entries(data)) {
    if (Array.isArray(value)) {
      if (value.length === 0) lines.push(`${key}: []`);
      else {
        lines.push(`${key}:`);
        for (const item of value) lines.push(`  - "${String(item)}"`);
      }
    } else if (value === null || value === undefined) {
      lines.push(`${key}: ""`);
    } else {
      const str = String(value);
      if (str.includes(":") || str.includes("#") || str.includes('"') || str === "") {
        lines.push(`${key}: "${str.replace(/"/g, '\\"')}"`);
      } else {
        lines.push(`${key}: ${str}`);
      }
    }
  }
  return lines.join("\n");
}

function rebuildFile(data: Frontmatter, content: string): string {
  return `---\n${serializeFrontmatter(data)}\n---\n\n${content}`;
}

async function findFileBySlug(slug: string): Promise<string | null> {
  const queuePath = join(VAULT_PATH, QUEUE_DIR);
  let files: string[];
  try {
    files = await readdir(queuePath);
  } catch {
    return null;
  }
  const direct = `${slug}.md`;
  if (files.includes(direct)) return direct;
  for (const f of files) {
    if (f.endsWith(".md") && slugFromFilename(f) === slug) return f;
  }
  return null;
}

// ---------------------------------------------------------------------------
// POST /api/queue/:slug/reject
// ---------------------------------------------------------------------------

export async function POST(
  _request: NextRequest,
  { params }: { params: Promise<{ slug: string }> },
): Promise<NextResponse> {
  const { slug } = await params;

  try {
    const filename = await findFileBySlug(slug);
    if (!filename) {
      return NextResponse.json({ error: "Item not found" }, { status: 404 });
    }

    const sourcePath = join(VAULT_PATH, QUEUE_DIR, filename);
    const raw = await readFile(sourcePath, "utf-8");
    const { data, content } = parseFrontmatter(raw);

    const now = new Date().toISOString();
    data.status = "rejected";
    data.modified = now;
    data.qualified_by = "web";

    const rejectedDir = join(VAULT_PATH, ARCHIVE_DIR, "rejected");
    await mkdir(rejectedDir, { recursive: true });

    const destPath = join(rejectedDir, filename);
    await writeFile(destPath, rebuildFile(data, content), "utf-8");
    await unlink(sourcePath);

    return NextResponse.json({ success: true });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to reject item";
    console.error(`POST /api/queue/${slug}/reject:`, message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
