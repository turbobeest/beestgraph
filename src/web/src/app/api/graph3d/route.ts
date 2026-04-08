import { NextRequest, NextResponse } from "next/server";

import { graphQuery } from "@/lib/falkordb";

// ─── Types ─────────────────────────────────────────────────────────────────

interface Graph3DNode {
  id: string;
  label: string;
  display_name: string;
  properties: Record<string, string | number | boolean | null>;
}

interface Graph3DEdge {
  source: string;
  target: string;
  type: string;
}

// ─── View definitions ───────────────────────────────────────────────────────

const VIEWS: Record<string, { label: string; edgeTypes: string[] | null }> = {
  all:         { label: "All",         edgeTypes: null },
  topics:      { label: "Topics",      edgeTypes: ["BELONGS_TO", "SUBTOPIC_OF"] },
  tags:        { label: "Tags",        edgeTypes: ["TAGGED_WITH"] },
  entities:    { label: "Entities",    edgeTypes: ["MENTIONS"] },
  links:       { label: "Links",       edgeTypes: ["LINKS_TO"] },
  sources:     { label: "Sources",     edgeTypes: ["DERIVED_FROM"] },
  connections: { label: "Connections", edgeTypes: ["SUPPORTS", "CONTRADICTS", "EXTENDS", "CHILD_OF"] },
};

// ─── Per-label queries returning scalar columns ─────────────────────────────

const NODE_QUERIES: Array<{ label: string; cypher: string; props: string[] }> = [
  {
    label: "Document",
    cypher: "MATCH (n:Document) WHERE NOT n.path STARTS WITH '00-meta/beestgraph/' RETURN id(n), n.title, n.path, n.status, n.type, n.importance, n.summary, n.uid, n.confidence, n.content_stage",
    props: ["title", "path", "status", "type", "importance", "summary", "uid", "confidence", "content_stage"],
  },
  { label: "Tag", cypher: "MATCH (n:Tag) RETURN id(n), n.name, n.normalized_name", props: ["name", "normalized_name"] },
  { label: "Topic", cypher: "MATCH (n:Topic) RETURN id(n), n.name, n.level", props: ["name", "level"] },
  { label: "Person", cypher: "MATCH (n:Person) RETURN id(n), n.name, n.normalized_name", props: ["name", "normalized_name"] },
  { label: "Concept", cypher: "MATCH (n:Concept) RETURN id(n), n.name, n.normalized_name, n.description", props: ["name", "normalized_name", "description"] },
  { label: "Organization", cypher: "MATCH (n:Organization) RETURN id(n), n.name, n.normalized_name", props: ["name", "normalized_name"] },
  { label: "Tool", cypher: "MATCH (n:Tool) RETURN id(n), n.name, n.normalized_name, n.url", props: ["name", "normalized_name", "url"] },
  { label: "Place", cypher: "MATCH (n:Place) RETURN id(n), n.name, n.normalized_name", props: ["name", "normalized_name"] },
  { label: "Source", cypher: "MATCH (n:Source) RETURN id(n), n.url, n.domain, n.name", props: ["url", "domain", "name"] },
];

const ALL_EDGE_TYPES = [
  "TAGGED_WITH", "BELONGS_TO", "MENTIONS", "LINKS_TO",
  "DERIVED_FROM", "SUPPORTS", "CONTRADICTS", "EXTENDS",
  "CHILD_OF", "SUBTOPIC_OF", "RELATED_TO", "SUPERSEDES", "INSPIRED_BY",
];

async function fetchGraph(edgeTypes: string[] | null) {
  const nodes = new Map<string, Graph3DNode>();
  const edges: Graph3DEdge[] = [];

  // Fetch all node types
  for (const nq of NODE_QUERIES) {
    try {
      const result = await graphQuery(nq.cypher);
      for (const row of result.rows) {
        const nodeId = `${nq.label}-${row[0]}`;
        const properties: Record<string, string | number | boolean | null> = {};
        nq.props.forEach((prop, i) => {
          properties[prop] = (row[i + 1] ?? null) as string | number | boolean | null;
        });
        nodes.set(nodeId, {
          id: nodeId,
          label: nq.label,
          display_name: String(properties.title ?? properties.name ?? properties.url ?? ""),
          properties,
        });
      }
    } catch { /* label may not exist yet */ }
  }

  // Fetch edges by type
  for (const et of (edgeTypes ?? ALL_EDGE_TYPES)) {
    try {
      const result = await graphQuery(
        `MATCH (a)-[r:${et}]->(b) RETURN id(a), labels(a)[0], id(b), labels(b)[0]`
      );
      for (const row of result.rows) {
        const srcId = `${row[1]}-${row[0]}`;
        const tgtId = `${row[3]}-${row[2]}`;
        if (nodes.has(srcId) && nodes.has(tgtId)) {
          edges.push({ source: srcId, target: tgtId, type: et });
        }
      }
    } catch { /* edge type may not exist */ }
  }

  return { nodes: Array.from(nodes.values()), edges };
}

// ─── GET /api/graph3d ───────────────────────────────────────────────────────

export async function GET(request: NextRequest): Promise<NextResponse> {
  const view = request.nextUrl.searchParams.get("view") ?? "all";

  if (view === "views") {
    return NextResponse.json(
      Object.entries(VIEWS).map(([id, v]) => ({ id, label: v.label }))
    );
  }

  try {
    const viewDef = VIEWS[view] ?? VIEWS["all"]!;
    const data = await fetchGraph(viewDef.edgeTypes);
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to query graph";
    console.error("GET /api/graph3d:", message);
    return NextResponse.json({ error: message, nodes: [], edges: [] }, { status: 500 });
  }
}
