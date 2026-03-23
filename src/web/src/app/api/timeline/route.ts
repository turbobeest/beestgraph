import { NextRequest, NextResponse } from "next/server";

import { getTimelineDocuments } from "@/lib/falkordb";

export async function GET(request: NextRequest): Promise<NextResponse> {
  const { searchParams } = request.nextUrl;
  const limit = Math.min(Math.max(parseInt(searchParams.get("limit") ?? "50", 10) || 50, 1), 500);

  try {
    const documents = await getTimelineDocuments(limit);
    return NextResponse.json({ documents });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to fetch timeline";
    console.error("GET /api/timeline:", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
