import { NextResponse } from "next/server";

import { getStats } from "@/lib/falkordb";

export async function GET(): Promise<NextResponse> {
  try {
    const stats = await getStats();
    return NextResponse.json(stats);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to fetch stats";
    console.error("GET /api/stats:", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
