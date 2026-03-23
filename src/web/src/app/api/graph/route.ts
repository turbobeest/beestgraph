import { NextRequest, NextResponse } from "next/server";

import { getTopics, queryGraph } from "@/lib/falkordb";

export async function GET(request: NextRequest): Promise<NextResponse> {
  const { searchParams } = request.nextUrl;

  const topicsOnly = searchParams.get("topicsOnly");
  if (topicsOnly === "true") {
    try {
      const topics = await getTopics();
      return NextResponse.json({ topics });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch topics";
      console.error("GET /api/graph (topics):", message);
      return NextResponse.json({ error: message }, { status: 500 });
    }
  }

  const topic = searchParams.get("topic") ?? undefined;
  const search = searchParams.get("search") ?? undefined;

  try {
    const data = await queryGraph(topic, search);
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to query graph";
    console.error("GET /api/graph:", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
