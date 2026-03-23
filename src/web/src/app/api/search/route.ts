import { NextRequest, NextResponse } from "next/server";

import { getRecentDocuments, searchDocuments } from "@/lib/falkordb";

export async function GET(request: NextRequest): Promise<NextResponse> {
  const { searchParams } = request.nextUrl;
  const query = searchParams.get("q");
  const recent = searchParams.get("recent");

  try {
    if (recent === "true") {
      const documents = await getRecentDocuments(20);
      return NextResponse.json({ documents });
    }

    if (!query || !query.trim()) {
      return NextResponse.json(
        { error: "Query parameter 'q' is required when 'recent' is not set" },
        { status: 400 },
      );
    }

    const documents = await searchDocuments(query.trim());
    return NextResponse.json({ documents });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Search failed";
    console.error("GET /api/search:", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
