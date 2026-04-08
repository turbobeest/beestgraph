import { NextRequest, NextResponse } from "next/server";

import { graphQuery } from "@/lib/falkordb";

interface SearchResult {
  id: string;
  label: string;
  display_name: string;
  properties: Record<string, string | number | boolean | null>;
}

// GET /api/graph3d/search?q=...
export async function GET(request: NextRequest): Promise<NextResponse> {
  const q = request.nextUrl.searchParams.get("q")?.trim() ?? "";

  if (q.length < 2) {
    return NextResponse.json({ results: [] });
  }

  try {
    // Search across multiple node types using CONTAINS (case-sensitive)
    // and toLower for case-insensitive matching
    const searchLower = q.toLowerCase();
    const queries = [
      {
        label: "Document",
        cypher: `MATCH (n:Document) WHERE toLower(n.title) CONTAINS $q RETURN id(n), n.title, n.path, n.status, n.type LIMIT 10`,
        props: ["title", "path", "status", "type"],
      },
      {
        label: "Tag",
        cypher: `MATCH (n:Tag) WHERE toLower(n.name) CONTAINS $q RETURN id(n), n.name, n.normalized_name LIMIT 10`,
        props: ["name", "normalized_name"],
      },
      {
        label: "Topic",
        cypher: `MATCH (n:Topic) WHERE toLower(n.name) CONTAINS $q RETURN id(n), n.name, n.level LIMIT 10`,
        props: ["name", "level"],
      },
      {
        label: "Person",
        cypher: `MATCH (n:Person) WHERE toLower(n.name) CONTAINS $q RETURN id(n), n.name, n.normalized_name LIMIT 10`,
        props: ["name", "normalized_name"],
      },
      {
        label: "Concept",
        cypher: `MATCH (n:Concept) WHERE toLower(n.name) CONTAINS $q RETURN id(n), n.name, n.normalized_name LIMIT 10`,
        props: ["name", "normalized_name"],
      },
      {
        label: "Tool",
        cypher: `MATCH (n:Tool) WHERE toLower(n.name) CONTAINS $q RETURN id(n), n.name, n.normalized_name LIMIT 10`,
        props: ["name", "normalized_name"],
      },
      {
        label: "Organization",
        cypher: `MATCH (n:Organization) WHERE toLower(n.name) CONTAINS $q RETURN id(n), n.name, n.normalized_name LIMIT 10`,
        props: ["name", "normalized_name"],
      },
      {
        label: "Source",
        cypher: `MATCH (n:Source) WHERE toLower(n.url) CONTAINS $q OR toLower(n.name) CONTAINS $q RETURN id(n), n.url, n.name LIMIT 10`,
        props: ["url", "name"],
      },
    ];

    const results: SearchResult[] = [];

    for (const sq of queries) {
      try {
        const result = await graphQuery(sq.cypher, { q: searchLower });
        for (const row of result.rows) {
          const nodeId = `${sq.label}-${row[0]}`;
          const properties: Record<string, string | number | boolean | null> = {};
          sq.props.forEach((prop, i) => {
            properties[prop] = (row[i + 1] ?? null) as string | number | boolean | null;
          });
          results.push({
            id: nodeId,
            label: sq.label,
            display_name: String(properties.title ?? properties.name ?? properties.url ?? ""),
            properties,
          });
        }
      } catch { /* skip labels that don't exist */ }
    }

    return NextResponse.json({ results: results.slice(0, 20) });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Search failed";
    console.error("GET /api/graph3d/search:", message);
    return NextResponse.json({ error: message, results: [] }, { status: 500 });
  }
}
