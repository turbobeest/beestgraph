import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

const CONFIG_PATH = path.join(
  process.env.HOME ?? "/home/turbobeest",
  "beestgraph",
  "config",
  "audit-recommendations.json",
);

interface Recommendation {
  id: string;
  file: string;
  title: string;
  agent: string;
  timestamp: string;
  intent: string;
  categorization: {
    para: { current: string; recommended: string; justification: string };
    zett: { current: string; recommended: string; justification: string };
    tree: { current: string; recommended: string; justification: string };
    atlas: { current: string; recommended: string; justification: string };
    graph: { current: string; recommended: string; justification: string };
  };
  enrichment: string;
  metadata: string;
  interlinking: string[];
  status: "pending" | "approved" | "deferred";
  defer_note: string;
}

interface AuditData {
  recommendations: Recommendation[];
}

function readAudit(): AuditData {
  const raw = fs.readFileSync(CONFIG_PATH, "utf-8");
  return JSON.parse(raw) as AuditData;
}

function writeAudit(data: AuditData): void {
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(data, null, 2) + "\n", "utf-8");
}

// GET /api/audit — return all recommendations
export async function GET(): Promise<NextResponse> {
  try {
    const data = readAudit();
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to read audit data";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

// POST /api/audit — add a new recommendation
export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json() as Recommendation;
    const data = readAudit();
    data.recommendations.push(body);
    writeAudit(data);
    return NextResponse.json({ success: true, total: data.recommendations.length });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to save recommendation";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

// PUT /api/audit — update status of a recommendation
export async function PUT(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json() as { id: string; status: string; defer_note?: string };
    const data = readAudit();
    const rec = data.recommendations.find(r => r.id === body.id);
    if (!rec) {
      return NextResponse.json({ error: "Recommendation not found" }, { status: 404 });
    }
    rec.status = body.status as "pending" | "approved" | "deferred";
    if (body.defer_note !== undefined) rec.defer_note = body.defer_note;
    writeAudit(data);
    return NextResponse.json({ success: true });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to update recommendation";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

// DELETE /api/audit — remove recommendation(s).
// Body shapes accepted:
//   { id: "..." }              → remove one by id (original behavior)
//   { status: "approved" }     → remove every recommendation matching that status
export async function DELETE(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json() as { id?: string; status?: string };
    const data = readAudit();
    const before = data.recommendations.length;

    if (body.id) {
      data.recommendations = data.recommendations.filter(r => r.id !== body.id);
      if (data.recommendations.length === before) {
        return NextResponse.json({ error: "Not found" }, { status: 404 });
      }
    } else if (body.status) {
      data.recommendations = data.recommendations.filter(r => r.status !== body.status);
    } else {
      return NextResponse.json({ error: "Must provide id or status" }, { status: 400 });
    }

    writeAudit(data);
    return NextResponse.json({
      success: true,
      removed: before - data.recommendations.length,
      remaining: data.recommendations.length,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to delete recommendation";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
