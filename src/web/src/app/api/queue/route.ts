import { readdir, readFile } from "node:fs/promises";
import { join } from "node:path";

import { NextResponse } from "next/server";

import { slugFromFilename } from "@/lib/queue";
import type { QueueItem } from "@/lib/queue";

const VAULT_PATH = process.env.VAULT_PATH ?? join(process.env.HOME ?? "/root", "vault");
const QUEUE_DIR = process.env.QUEUE_DIR ?? "02-queue";

interface Frontmatter {
  title?: string;
  type?: string;
  topics?: string[];
  tags?: string[];
  visibility?: string;
  quality?: string;
  summary?: string;
  security_findings?: string;
  date_captured?: string;
  source_url?: string;
  [key: string]: unknown;
}

function parseFrontmatter(raw: string): { data: Frontmatter; content: string } {
  if (!raw.startsWith("---")) {
    return { data: {}, content: raw };
  }
  const end = raw.indexOf("---", 3);
  if (end === -1) {
    return { data: {}, content: raw };
  }
  const yamlBlock = raw.slice(3, end).trim();
  const content = raw.slice(end + 3).trim();

  // Simple YAML parser for frontmatter — handles the fields we need.
  // We use a line-by-line approach for robustness without gray-matter at runtime.
  const data: Record<string, unknown> = {};
  let currentKey = "";
  let currentList: string[] | null = null;

  for (const line of yamlBlock.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;

    // List item
    if (trimmed.startsWith("- ") && currentList !== null) {
      let val = trimmed.slice(2).trim();
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }
      currentList.push(val);
      continue;
    }

    // Key-value pair
    const colonIdx = trimmed.indexOf(":");
    if (colonIdx > 0) {
      // Save previous list
      if (currentList !== null && currentKey) {
        data[currentKey] = currentList;
      }
      currentList = null;

      const key = trimmed.slice(0, colonIdx).trim();
      let val = trimmed.slice(colonIdx + 1).trim();
      currentKey = key;

      if (val === "" || val === "[]") {
        // Could be a list starting on next line, or empty value
        if (val === "[]") {
          data[key] = [];
        } else {
          currentList = [];
        }
        continue;
      }

      // Inline list: [a, b, c]
      if (val.startsWith("[") && val.endsWith("]")) {
        const inner = val.slice(1, -1);
        data[key] = inner
          ? inner.split(",").map((s) => {
              let v = s.trim();
              if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
                v = v.slice(1, -1);
              }
              return v;
            })
          : [];
        continue;
      }

      // Strip quotes
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }
      data[key] = val;
    }
  }

  // Flush last list
  if (currentList !== null && currentKey) {
    data[currentKey] = currentList;
  }

  return { data: data as Frontmatter, content };
}

export async function GET(): Promise<NextResponse> {
  const queuePath = join(VAULT_PATH, QUEUE_DIR);

  try {
    let files: string[];
    try {
      files = await readdir(queuePath);
    } catch {
      // Directory doesn't exist yet — return empty list
      return NextResponse.json({ items: [], count: 0 });
    }

    const mdFiles = files.filter((f) => f.endsWith(".md")).sort();

    const items: QueueItem[] = [];

    for (const filename of mdFiles) {
      try {
        const raw = await readFile(join(queuePath, filename), "utf-8");
        const { data } = parseFrontmatter(raw);

        const topics = Array.isArray(data.topics) ? data.topics : [];

        items.push({
          slug: slugFromFilename(filename),
          title: String(data.title ?? filename.replace(/\.md$/i, "")),
          type: String(data.type ?? ""),
          topic: topics[0] ?? "",
          tags: Array.isArray(data.tags) ? data.tags.map(String) : [],
          visibility: String(data.visibility ?? "private"),
          quality: String(data.quality ?? ""),
          summary: String(data.summary ?? ""),
          securityFindings: String(data.security_findings ?? ""),
          filename,
          dateCaptured: String(data.date_captured ?? ""),
          sourceUrl: String(data.source_url ?? ""),
        });
      } catch (err) {
        console.error(`Failed to read queue file ${filename}:`, err);
      }
    }

    // Sort by date_captured DESC (newest first)
    items.sort((a, b) => {
      if (!a.dateCaptured && !b.dateCaptured) return 0;
      if (!a.dateCaptured) return 1;
      if (!b.dateCaptured) return -1;
      return b.dateCaptured.localeCompare(a.dateCaptured);
    });

    return NextResponse.json({ items, count: items.length });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to list queue";
    console.error("GET /api/queue:", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
