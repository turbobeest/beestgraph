import { createClient } from "redis";

const FALKORDB_HOST = process.env.FALKORDB_HOST ?? "localhost";
const FALKORDB_PORT = parseInt(process.env.FALKORDB_PORT ?? "6379", 10);
const GRAPH_NAME = "beestgraph";

type RedisClient = ReturnType<typeof createClient>;
let clientInstance: RedisClient | null = null;

async function getClient(): Promise<RedisClient> {
  if (clientInstance) return clientInstance;
  clientInstance = createClient({
    socket: { host: FALKORDB_HOST, port: FALKORDB_PORT },
  });
  await clientInstance.connect();
  return clientInstance;
}

/** Run a Cypher query via GRAPH.QUERY and return parsed rows. */
async function graphQuery(
  cypher: string,
  params?: Record<string, string | number>,
): Promise<{ headers: string[]; rows: unknown[][]; metadata: string[] }> {
  const client = await getClient();
  const paramStr = params
    ? "CYPHER " +
      Object.entries(params)
        .map(([k, v]) => `${k}=${typeof v === "string" ? `"${v.replace(/"/g, '\\"')}"` : v}`)
        .join(" ") +
      " "
    : "";

  const raw = (await client.sendCommand([
    "GRAPH.QUERY",
    GRAPH_NAME,
    `${paramStr}${cypher}`,
    "--compact",
  ])) as unknown[];

  if (!Array.isArray(raw) || raw.length === 0) {
    return { headers: [], rows: [], metadata: [] };
  }

  // FalkorDB returns [headers, data, metadata] or [metadata]
  if (raw.length === 1) {
    return { headers: [], rows: [], metadata: raw[0] as string[] };
  }

  const headers = (raw[0] as Array<[number, string]>).map((h) => h[1]);
  const rows = raw[1] as unknown[][];
  const metadata = raw[2] as string[];

  // Each row contains [type, value] pairs in compact mode
  const parsedRows = rows.map((row) =>
    (row as Array<[number, unknown]>).map((cell) => {
      const [cellType, cellValue] = cell;
      // Type 2 = integer, 3 = string, 4 = double, 1 = null
      if (cellType === 2) return Number(cellValue);
      if (cellType === 3) return String(cellValue);
      if (cellType === 4) return Number(cellValue);
      return cellValue;
    }),
  );

  return { headers, rows: parsedRows, metadata };
}

export interface GraphNode {
  id: string;
  label: string;
  properties: Record<string, string | number | boolean | null>;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
  properties: Record<string, string | number | boolean | null>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface DocumentRecord {
  path: string;
  title: string;
  summary: string;
  status: string;
  sourceType: string;
  sourceUrl: string;
  createdAt: string;
  updatedAt: string;
}

export interface StatsResult {
  documents: number;
  topics: number;
  tags: number;
  sources: number;
}

export async function queryGraph(
  topicFilter?: string,
  searchTerm?: string,
  limit: number = 200,
): Promise<GraphData> {
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];
  const seenNodeIds = new Set<string>();

  const conditions: string[] = [];
  if (topicFilter) conditions.push("t.name = $topicFilter");
  if (searchTerm) {
    conditions.push("(d.title CONTAINS $searchTerm OR d.summary CONTAINS $searchTerm)");
  }
  const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

  const params: Record<string, string | number> = { limit };
  if (topicFilter) params["topicFilter"] = topicFilter;
  if (searchTerm) params["searchTerm"] = searchTerm;

  const result = await graphQuery(
    `MATCH (d:Document)-[:BELONGS_TO]->(t:Topic)
     ${whereClause}
     RETURN d.path, d.title, d.summary, d.status, t.name
     LIMIT $limit`,
    params,
  );

  for (const row of result.rows) {
    const [docPath, docTitle, docSummary, docStatus, topicName] = row as string[];
    const docId = `doc-${docPath ?? "unknown"}`;
    const topicId = `topic-${topicName ?? "unknown"}`;

    if (!seenNodeIds.has(docId)) {
      seenNodeIds.add(docId);
      nodes.push({
        id: docId,
        label: "Document",
        properties: {
          title: docTitle ?? "",
          path: docPath ?? "",
          summary: docSummary ?? "",
          status: docStatus ?? "",
        },
      });
    }
    if (!seenNodeIds.has(topicId)) {
      seenNodeIds.add(topicId);
      nodes.push({ id: topicId, label: "Topic", properties: { name: topicName ?? "" } });
    }
    edges.push({ source: docId, target: topicId, relationship: "BELONGS_TO", properties: {} });
  }

  // Tag relationships
  const tagWhere = searchTerm
    ? "WHERE d.title CONTAINS $searchTerm OR d.summary CONTAINS $searchTerm"
    : "";
  const tagResult = await graphQuery(
    `MATCH (d:Document)-[:TAGGED_WITH]->(tag:Tag)
     ${tagWhere}
     RETURN d.path, d.title, d.summary, d.status, tag.name, tag.normalized_name
     LIMIT $limit`,
    params,
  );

  for (const row of tagResult.rows) {
    const [docPath, docTitle, docSummary, docStatus, tagName, tagNorm] = row as string[];
    const docId = `doc-${docPath ?? "unknown"}`;
    const tagId = `tag-${tagNorm ?? tagName ?? "unknown"}`;

    if (!seenNodeIds.has(docId)) {
      seenNodeIds.add(docId);
      nodes.push({
        id: docId,
        label: "Document",
        properties: {
          title: docTitle ?? "",
          path: docPath ?? "",
          summary: docSummary ?? "",
          status: docStatus ?? "",
        },
      });
    }
    if (!seenNodeIds.has(tagId)) {
      seenNodeIds.add(tagId);
      nodes.push({ id: tagId, label: "Tag", properties: { name: tagName ?? "" } });
    }
    edges.push({ source: docId, target: tagId, relationship: "TAGGED_WITH", properties: {} });
  }

  return { nodes, edges };
}

export async function searchDocuments(
  query: string,
  limit: number = 50,
): Promise<DocumentRecord[]> {
  const result = await graphQuery(
    `CALL db.idx.fulltext.queryNodes('Document', $query)
     YIELD node
     RETURN node.path, node.title, node.summary, node.status,
            node.source_type, node.source_url, node.created_at, node.updated_at
     LIMIT $limit`,
    { query, limit },
  );

  return result.rows.map((row) => ({
    path: String(row[0] ?? ""),
    title: String(row[1] ?? ""),
    summary: String(row[2] ?? ""),
    status: String(row[3] ?? ""),
    sourceType: String(row[4] ?? ""),
    sourceUrl: String(row[5] ?? ""),
    createdAt: String(row[6] ?? ""),
    updatedAt: String(row[7] ?? ""),
  }));
}

export async function getRecentDocuments(limit: number = 20): Promise<DocumentRecord[]> {
  const result = await graphQuery(
    `MATCH (d:Document)
     RETURN d.path, d.title, d.summary, d.status,
            d.source_type, d.source_url, d.created_at, d.updated_at
     ORDER BY d.created_at DESC
     LIMIT $limit`,
    { limit },
  );

  return result.rows.map((row) => ({
    path: String(row[0] ?? ""),
    title: String(row[1] ?? ""),
    summary: String(row[2] ?? ""),
    status: String(row[3] ?? ""),
    sourceType: String(row[4] ?? ""),
    sourceUrl: String(row[5] ?? ""),
    createdAt: String(row[6] ?? ""),
    updatedAt: String(row[7] ?? ""),
  }));
}

export async function getStats(): Promise<StatsResult> {
  const [docs, topics, tags, sources] = await Promise.all([
    graphQuery("MATCH (d:Document) RETURN count(d)"),
    graphQuery("MATCH (t:Topic) RETURN count(t)"),
    graphQuery("MATCH (t:Tag) RETURN count(t)"),
    graphQuery("MATCH (s:Source) RETURN count(s)"),
  ]);

  const extractCount = (r: Awaited<ReturnType<typeof graphQuery>>): number =>
    r.rows.length > 0 ? Number(r.rows[0]?.[0] ?? 0) : 0;

  return {
    documents: extractCount(docs),
    topics: extractCount(topics),
    tags: extractCount(tags),
    sources: extractCount(sources),
  };
}

export async function createEntry(entry: {
  url: string;
  title: string;
  notes: string;
  tags: string[];
}): Promise<{ path: string }> {
  const now = new Date().toISOString();
  const slug = entry.title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  const path = `inbox/${slug}.md`;

  await graphQuery(
    `MERGE (d:Document {path: $path})
     SET d.title = $title, d.source_url = $url, d.source_type = 'manual',
         d.status = 'inbox', d.content = $notes,
         d.created_at = $now, d.updated_at = $now
     RETURN d.path`,
    { path, title: entry.title, url: entry.url, notes: entry.notes, now },
  );

  for (const tagName of entry.tags) {
    const normalizedName = tagName.toLowerCase().trim();
    await graphQuery(
      `MERGE (t:Tag {normalized_name: $normalizedName})
       ON CREATE SET t.name = $tagName
       WITH t
       MATCH (d:Document {path: $path})
       MERGE (d)-[:TAGGED_WITH]->(t)`,
      { normalizedName, tagName, path },
    );
  }

  return { path };
}

export async function getTopics(): Promise<Array<{ name: string; level: number }>> {
  const result = await graphQuery(
    `MATCH (t:Topic)
     RETURN t.name, t.level
     ORDER BY t.level ASC, t.name ASC`,
  );

  return result.rows.map((row) => ({
    name: String(row[0] ?? ""),
    level: Number(row[1] ?? 0),
  }));
}

export async function closeConnection(): Promise<void> {
  if (clientInstance) {
    await clientInstance.disconnect();
    clientInstance = null;
  }
}
