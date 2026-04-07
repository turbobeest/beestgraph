import { readdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";

import { NextRequest, NextResponse } from "next/server";

import { slugFromFilename, LEGACY_TYPE_MAP, LEGACY_QUALITY_MAP } from "@/lib/queue";
import type { QueueItemDetail, UpdateBody } from "@/lib/queue";

const VAULT_PATH = process.env.VAULT_PATH ?? join(process.env.HOME ?? "/root", "vault");
const QUEUE_DIR = process.env.QUEUE_DIR ?? "02-queue";

// ---------------------------------------------------------------------------
// Frontmatter helpers
// ---------------------------------------------------------------------------

interface Frontmatter {
  [key: string]: unknown;
}

function parseFrontmatter(raw: string): { data: Frontmatter; content: string; rawYaml: string } {
  if (!raw.startsWith("---")) {
    return { data: {}, content: raw, rawYaml: "" };
  }
  const end = raw.indexOf("---", 3);
  if (end === -1) {
    return { data: {}, content: raw, rawYaml: "" };
  }
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
      if (currentList !== null && currentKey) {
        data[currentKey] = currentList;
      }
      currentList = null;

      const key = trimmed.slice(0, colonIdx).trim();
      let val = trimmed.slice(colonIdx + 1).trim();
      currentKey = key;

      if (val === "" || val === "[]") {
        if (val === "[]") {
          data[key] = [];
        } else {
          currentList = [];
        }
        continue;
      }

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

      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }
      data[key] = val;
    }
  }

  if (currentList !== null && currentKey) {
    data[currentKey] = currentList;
  }

  return { data, content, rawYaml: yamlBlock };
}

function serializeFrontmatter(data: Frontmatter): string {
  const lines: string[] = [];
  for (const [key, value] of Object.entries(data)) {
    if (Array.isArray(value)) {
      if (value.length === 0) {
        lines.push(`${key}: []`);
      } else {
        lines.push(`${key}:`);
        for (const item of value) {
          lines.push(`  - "${String(item)}"`);
        }
      }
    } else if (value === null || value === undefined) {
      lines.push(`${key}: ""`);
    } else {
      const str = String(value);
      // Quote strings that might cause YAML issues
      if (str.includes(":") || str.includes("#") || str.includes('"') || str.includes("'") || str === "") {
        lines.push(`${key}: "${str.replace(/"/g, '\\"')}"`);
      } else {
        lines.push(`${key}: ${str}`);
      }
    }
  }
  return lines.join("\n");
}

function rebuildFile(data: Frontmatter, content: string): string {
  const yaml = serializeFrontmatter(data);
  return `---\n${yaml}\n---\n\n${content}`;
}

// ---------------------------------------------------------------------------
// Find file by slug
// ---------------------------------------------------------------------------

async function findFileBySlug(slug: string): Promise<string | null> {
  const queuePath = join(VAULT_PATH, QUEUE_DIR);
  let files: string[];
  try {
    files = await readdir(queuePath);
  } catch {
    return null;
  }

  // Direct match first
  const direct = `${slug}.md`;
  if (files.includes(direct)) return direct;

  // Fuzzy: check slug generation for each file
  for (const f of files) {
    if (f.endsWith(".md") && slugFromFilename(f) === slug) {
      return f;
    }
  }

  return null;
}

// ---------------------------------------------------------------------------
// GET /api/queue/:slug
// ---------------------------------------------------------------------------

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ slug: string }> },
): Promise<NextResponse> {
  const { slug } = await params;

  try {
    const filename = await findFileBySlug(slug);
    if (!filename) {
      return NextResponse.json({ error: "Item not found" }, { status: 404 });
    }

    const raw = await readFile(join(VAULT_PATH, QUEUE_DIR, filename), "utf-8");
    const { data, content } = parseFrontmatter(raw);

    const topics = Array.isArray(data.topics) ? (data.topics as string[]) : [];
    const tags = Array.isArray(data.tags) ? (data.tags as string[]).map(String) : [];

    // Resolve type with backwards compat for legacy names
    const rawType = String(data.type ?? data.content_type ?? "");
    const resolvedType = LEGACY_TYPE_MAP[rawType] ?? rawType;

    // Resolve confidence: prefer numeric confidence, fall back from legacy quality
    let confidence: number | null = null;
    if (data.confidence !== undefined && data.confidence !== "") {
      confidence = Number(data.confidence);
    } else if (data.quality) {
      confidence = LEGACY_QUALITY_MAP[String(data.quality)] ?? null;
    }

    // Resolve source_url: check both flat and nested forms
    const sourceUrl = String(
      data.source_url ?? (data.source as Record<string, unknown> | undefined)?.url ?? "",
    );

    // Resolve date_captured: check both flat and nested forms
    const dateCaptured = String(
      data.date_captured ?? (data.dates as Record<string, unknown> | undefined)?.captured ?? "",
    );

    const item: QueueItemDetail = {
      slug,
      title: String(data.title ?? filename.replace(/\.md$/i, "")),
      type: resolvedType,
      topic: topics[0] ?? "",
      tags,
      confidence,
      summary: String(data.summary ?? ""),
      securityFindings: String(data.security_findings ?? ""),
      filename,
      dateCaptured,
      sourceUrl,
      content,
      frontmatter: data,
    };

    return NextResponse.json(item);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to get queue item";
    console.error(`GET /api/queue/${slug}:`, message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

// ---------------------------------------------------------------------------
// POST /api/queue/:slug — update item fields
// ---------------------------------------------------------------------------

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ slug: string }> },
): Promise<NextResponse> {
  const { slug } = await params;

  let body: UpdateBody;
  try {
    body = (await request.json()) as UpdateBody;
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  try {
    const filename = await findFileBySlug(slug);
    if (!filename) {
      return NextResponse.json({ error: "Item not found" }, { status: 404 });
    }

    const filePath = join(VAULT_PATH, QUEUE_DIR, filename);
    const raw = await readFile(filePath, "utf-8");
    const { data, content } = parseFrontmatter(raw);

    // Apply updates
    if (body.type !== undefined) data.type = body.type;
    if (body.topic !== undefined) {
      data.topics = body.topic ? [body.topic] : [];
    }
    if (body.tags !== undefined) data.tags = body.tags;
    if (body.confidence !== undefined) data.confidence = body.confidence;
    if (body.summary !== undefined) data.summary = body.summary;

    data.modified = new Date().toISOString();

    await writeFile(filePath, rebuildFile(data, content), "utf-8");

    const topics = Array.isArray(data.topics) ? (data.topics as string[]) : [];
    const tags = Array.isArray(data.tags) ? (data.tags as string[]).map(String) : [];

    // Resolve type for response
    const respRawType = String(data.type ?? data.content_type ?? "");
    const respType = LEGACY_TYPE_MAP[respRawType] ?? respRawType;

    // Resolve confidence for response
    let respConfidence: number | null = null;
    if (data.confidence !== undefined && data.confidence !== "") {
      respConfidence = Number(data.confidence);
    } else if (data.quality) {
      respConfidence = LEGACY_QUALITY_MAP[String(data.quality)] ?? null;
    }

    return NextResponse.json({
      slug,
      title: String(data.title ?? ""),
      type: respType,
      topic: topics[0] ?? "",
      tags,
      confidence: respConfidence,
      summary: String(data.summary ?? ""),
      securityFindings: String(data.security_findings ?? ""),
      filename,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to update queue item";
    console.error(`POST /api/queue/${slug}:`, message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

// ---------------------------------------------------------------------------
// POST /api/queue/:slug/approve — handled via URL path check
// POST /api/queue/:slug/reject  — handled via URL path check
// ---------------------------------------------------------------------------

// These are handled by separate route files (approve/route.ts and reject/route.ts)
