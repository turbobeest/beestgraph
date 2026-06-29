import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

const CONFIG_PATH = path.join(
  process.env.HOME ?? "/home/turbobeest",
  "beestgraph",
  "config",
  "topic-tree.json",
);

interface SubNode {
  id: number;
  name: string;
  slug: string;
  subs: SubNode[];
}

interface Category {
  id: number;
  name: string;
  slug: string;
  subs: SubNode[];
}

interface Area {
  id: number;
  name: string;
  slug: string;
  categories: Category[];
}

interface TopicTree {
  areas: Area[];
}

function readTree(): TopicTree {
  const raw = fs.readFileSync(CONFIG_PATH, "utf-8");
  return JSON.parse(raw) as TopicTree;
}

function writeTree(tree: TopicTree): void {
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(tree, null, 2) + "\n", "utf-8");
}

function isValidSubs(subs: unknown[], depth: number): boolean {
  if (depth > 10) return false; // safety limit
  for (const s of subs) {
    if (typeof s !== "object" || s === null) return false;
    const n = s as Record<string, unknown>;
    if (typeof n["id"] !== "number") return false;
    if (typeof n["name"] !== "string") return false;
    if (typeof n["slug"] !== "string") return false;
    if (!Array.isArray(n["subs"])) return false;
    if (!isValidSubs(n["subs"] as unknown[], depth + 1)) return false;
  }
  return true;
}

function isValidTree(data: unknown): data is TopicTree {
  if (typeof data !== "object" || data === null) return false;
  const obj = data as Record<string, unknown>;
  if (!Array.isArray(obj["areas"])) return false;
  for (const area of obj["areas"] as unknown[]) {
    if (typeof area !== "object" || area === null) return false;
    const a = area as Record<string, unknown>;
    if (typeof a["id"] !== "number") return false;
    if (typeof a["name"] !== "string") return false;
    if (typeof a["slug"] !== "string") return false;
    if (!Array.isArray(a["categories"])) return false;
    for (const cat of a["categories"] as unknown[]) {
      if (typeof cat !== "object" || cat === null) return false;
      const c = cat as Record<string, unknown>;
      if (typeof c["id"] !== "number") return false;
      if (typeof c["name"] !== "string") return false;
      if (typeof c["slug"] !== "string") return false;
      if (!Array.isArray(c["subs"])) return false;
      if (!isValidSubs(c["subs"] as unknown[], 0)) return false;
    }
  }
  return true;
}

// GET /api/org — return the current topic tree
export async function GET(): Promise<NextResponse> {
  try {
    const tree = readTree();
    return NextResponse.json(tree);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to read topic tree";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

// PUT /api/org — save updated topic tree
export async function PUT(request: NextRequest): Promise<NextResponse> {
  try {
    const body: unknown = await request.json();

    if (!isValidTree(body)) {
      return NextResponse.json(
        { error: "Invalid topic tree structure" },
        { status: 400 },
      );
    }

    writeTree(body);
    return NextResponse.json({ success: true, areas: body.areas.length });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to save topic tree";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
