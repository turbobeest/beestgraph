import { readdir, readFile, writeFile, mkdir, unlink } from "node:fs/promises";
import { join } from "node:path";

import { NextRequest, NextResponse } from "next/server";

import { graphQuery } from "@/lib/falkordb";
import { slugFromFilename } from "@/lib/queue";
import type { ApproveBody } from "@/lib/queue";

const VAULT_PATH = process.env.VAULT_PATH ?? join(process.env.HOME ?? "/root", "vault");
const QUEUE_DIR = process.env.QUEUE_DIR ?? "02-queue";
const FLEETING_DIR = process.env.FLEETING_DIR ?? "03-fleeting";
const RESOURCES_DIR = process.env.RESOURCES_DIR ?? "07-resources";

// ---------------------------------------------------------------------------
// Frontmatter helpers (duplicated for route isolation)
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
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }
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
      if (value.length === 0) {
        lines.push(`${key}: []`);
      } else {
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
// POST /api/queue/:slug/approve
// ---------------------------------------------------------------------------

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ slug: string }> },
): Promise<NextResponse> {
  const { slug } = await params;

  let body: ApproveBody;
  try {
    body = (await request.json()) as ApproveBody;
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const contentStage = body.content_stage ?? "fleeting";
  if (contentStage !== "fleeting" && contentStage !== "evergreen") {
    return NextResponse.json({ error: "content_stage must be 'fleeting' or 'evergreen'" }, { status: 400 });
  }

  try {
    const filename = await findFileBySlug(slug);
    if (!filename) {
      return NextResponse.json({ error: "Item not found" }, { status: 404 });
    }

    const sourcePath = join(VAULT_PATH, QUEUE_DIR, filename);
    const raw = await readFile(sourcePath, "utf-8");
    const { data, content } = parseFrontmatter(raw);

    const now = new Date().toISOString();
    data.modified = now;
    data.content_stage = contentStage;

    let destDir: string;
    let destination: string;

    if (contentStage === "fleeting") {
      data.status = "published";
      destDir = join(VAULT_PATH, FLEETING_DIR);
      destination = `${FLEETING_DIR}/${filename}`;
    } else {
      data.status = "published";
      data.published = now;
      const topic = Array.isArray(data.topics) && data.topics.length > 0
        ? String(data.topics[0])
        : "uncategorized";
      const topicDir = topic.replace(/\//g, "/");
      destDir = join(VAULT_PATH, RESOURCES_DIR, topicDir);
      destination = `${RESOURCES_DIR}/${topicDir}/${filename}`;
    }

    await mkdir(destDir, { recursive: true });
    const destPath = join(destDir, filename);
    await writeFile(destPath, rebuildFile(data, content), "utf-8");
    await unlink(sourcePath);

    // Ingest into FalkorDB
    try {
      const title = String(data.title ?? "");
      const summary = String(data.summary ?? "");
      const sourceUrl = String(
        data.source_url ?? (data.source as Record<string, unknown> | undefined)?.url ?? "",
      );
      const sourceType = String(
        data.source_type ?? (data.source as Record<string, unknown> | undefined)?.type ?? "manual",
      );
      const vaultPath = destination;

      await graphQuery(
        `MERGE (d:Document {path: $path})
         SET d.title = $title,
             d.summary = $summary,
             d.source_url = $sourceUrl,
             d.source_type = $sourceType,
             d.status = $status,
             d.updated_at = $now
         RETURN d.path`,
        {
          path: vaultPath,
          title,
          summary,
          sourceUrl,
          sourceType,
          status: "published",
          now,
        },
      );

      // Add topic relationship
      const topics = Array.isArray(data.topics) ? (data.topics as string[]) : [];
      for (const topicName of topics) {
        await graphQuery(
          `MERGE (t:Topic {name: $topicName})
           WITH t
           MATCH (d:Document {path: $path})
           MERGE (d)-[:BELONGS_TO]->(t)`,
          { topicName: String(topicName), path: vaultPath },
        );
      }

      // Add tag relationships
      const tags = Array.isArray(data.tags) ? (data.tags as string[]) : [];
      for (const tagName of tags) {
        const normalizedName = String(tagName).toLowerCase().trim();
        await graphQuery(
          `MERGE (t:Tag {normalized_name: $normalizedName})
           ON CREATE SET t.name = $tagName
           WITH t
           MATCH (d:Document {path: $path})
           MERGE (d)-[:TAGGED_WITH]->(t)`,
          { normalizedName, tagName: String(tagName), path: vaultPath },
        );
      }
    } catch (graphErr) {
      // Log but don't fail the approve — file was already moved
      console.error("FalkorDB ingestion error:", graphErr);
    }

    return NextResponse.json({ success: true, destination });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to approve item";
    console.error(`POST /api/queue/${slug}/approve:`, message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
