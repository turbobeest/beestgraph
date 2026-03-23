import { NextRequest, NextResponse } from "next/server";

import { createEntry } from "@/lib/falkordb";

interface EntryRequestBody {
  url?: string;
  title?: string;
  notes?: string;
  tags?: string[];
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  let body: EntryRequestBody;

  try {
    body = (await request.json()) as EntryRequestBody;
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const title = body.title?.trim();
  if (!title) {
    return NextResponse.json({ error: "Title is required" }, { status: 400 });
  }

  const url = body.url?.trim() ?? "";
  const notes = body.notes?.trim() ?? "";
  const tags = Array.isArray(body.tags) ? body.tags.filter((t) => typeof t === "string") : [];

  try {
    const result = await createEntry({ url, title, notes, tags });
    return NextResponse.json(result, { status: 201 });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to create entry";
    console.error("POST /api/entry:", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
