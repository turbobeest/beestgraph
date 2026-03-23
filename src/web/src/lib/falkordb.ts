import { FalkorDB, Graph } from "falkordb";

const FALKORDB_HOST = process.env.FALKORDB_HOST ?? "localhost";
const FALKORDB_PORT = parseInt(process.env.FALKORDB_PORT ?? "6379", 10);
const GRAPH_NAME = "beestgraph";

let clientInstance: FalkorDB | null = null;

async function getClient(): Promise<FalkorDB> {
  if (clientInstance) {
    return clientInstance;
  }
  clientInstance = await FalkorDB.connect({
    socket: {
      host: FALKORDB_HOST,
      port: FALKORDB_PORT,
    },
  });
  return clientInstance;
}

async function getGraph(): Promise<Graph> {
  const client = await getClient();
  return client.selectGraph(GRAPH_NAME);
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
  const graph = await getGraph();
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];
  const seenNodeIds = new Set<string>();

  let whereClause = "";
  if (topicFilter) {
    whereClause = `WHERE t.name = $topicFilter`;
  }
  if (searchTerm) {
    whereClause = whereClause
      ? `${whereClause} AND (d.title CONTAINS $searchTerm OR d.summary CONTAINS $searchTerm)`
      : `WHERE d.title CONTAINS $searchTerm OR d.summary CONTAINS $searchTerm`;
  }

  const query = `
    MATCH (d:Document)-[r:BELONGS_TO]->(t:Topic)
    ${whereClause}
    RETURN d, r, t
    LIMIT $limit
  `;

  const params: Record<string, string | number> = { limit };
  if (topicFilter) params["topicFilter"] = topicFilter;
  if (searchTerm) params["searchTerm"] = searchTerm;

  const result = await graph.query(query, { params });

  while (result.hasNext()) {
    const record = result.next();
    const doc = record.get("d") as Record<string, string>;
    const topic = record.get("t") as Record<string, string>;

    const docId = `doc-${doc["path"] ?? "unknown"}`;
    const topicId = `topic-${topic["name"] ?? "unknown"}`;

    if (!seenNodeIds.has(docId)) {
      seenNodeIds.add(docId);
      nodes.push({
        id: docId,
        label: "Document",
        properties: {
          title: doc["title"] ?? "",
          path: doc["path"] ?? "",
          summary: doc["summary"] ?? "",
          status: doc["status"] ?? "",
        },
      });
    }

    if (!seenNodeIds.has(topicId)) {
      seenNodeIds.add(topicId);
      nodes.push({
        id: topicId,
        label: "Topic",
        properties: {
          name: topic["name"] ?? "",
        },
      });
    }

    edges.push({
      source: docId,
      target: topicId,
      relationship: "BELONGS_TO",
      properties: {},
    });
  }

  const tagQuery = `
    MATCH (d:Document)-[r:TAGGED_WITH]->(tag:Tag)
    ${searchTerm ? "WHERE d.title CONTAINS $searchTerm OR d.summary CONTAINS $searchTerm" : ""}
    RETURN d, r, tag
    LIMIT $limit
  `;

  const tagResult = await graph.query(tagQuery, { params });

  while (tagResult.hasNext()) {
    const record = tagResult.next();
    const doc = record.get("d") as Record<string, string>;
    const tag = record.get("tag") as Record<string, string>;

    const docId = `doc-${doc["path"] ?? "unknown"}`;
    const tagId = `tag-${tag["normalized_name"] ?? tag["name"] ?? "unknown"}`;

    if (!seenNodeIds.has(docId)) {
      seenNodeIds.add(docId);
      nodes.push({
        id: docId,
        label: "Document",
        properties: {
          title: doc["title"] ?? "",
          path: doc["path"] ?? "",
          summary: doc["summary"] ?? "",
          status: doc["status"] ?? "",
        },
      });
    }

    if (!seenNodeIds.has(tagId)) {
      seenNodeIds.add(tagId);
      nodes.push({
        id: tagId,
        label: "Tag",
        properties: {
          name: tag["name"] ?? "",
        },
      });
    }

    edges.push({
      source: docId,
      target: tagId,
      relationship: "TAGGED_WITH",
      properties: {},
    });
  }

  return { nodes, edges };
}

export async function searchDocuments(
  query: string,
  limit: number = 50,
): Promise<DocumentRecord[]> {
  const graph = await getGraph();

  const cypher = `
    CALL db.idx.fulltext.queryNodes('Document', $query)
    YIELD node
    RETURN node
    LIMIT $limit
  `;

  const result = await graph.query(cypher, {
    params: { query, limit },
  });

  const documents: DocumentRecord[] = [];
  while (result.hasNext()) {
    const record = result.next();
    const node = record.get("node") as Record<string, string>;
    documents.push({
      path: node["path"] ?? "",
      title: node["title"] ?? "",
      summary: node["summary"] ?? "",
      status: node["status"] ?? "",
      sourceType: node["source_type"] ?? "",
      sourceUrl: node["source_url"] ?? "",
      createdAt: node["created_at"] ?? "",
      updatedAt: node["updated_at"] ?? "",
    });
  }

  return documents;
}

export async function getRecentDocuments(limit: number = 20): Promise<DocumentRecord[]> {
  const graph = await getGraph();

  const cypher = `
    MATCH (d:Document)
    RETURN d
    ORDER BY d.created_at DESC
    LIMIT $limit
  `;

  const result = await graph.query(cypher, { params: { limit } });

  const documents: DocumentRecord[] = [];
  while (result.hasNext()) {
    const record = result.next();
    const node = record.get("d") as Record<string, string>;
    documents.push({
      path: node["path"] ?? "",
      title: node["title"] ?? "",
      summary: node["summary"] ?? "",
      status: node["status"] ?? "",
      sourceType: node["source_type"] ?? "",
      sourceUrl: node["source_url"] ?? "",
      createdAt: node["created_at"] ?? "",
      updatedAt: node["updated_at"] ?? "",
    });
  }

  return documents;
}

export async function getStats(): Promise<StatsResult> {
  const graph = await getGraph();

  const queries = [
    "MATCH (d:Document) RETURN count(d) AS count",
    "MATCH (t:Topic) RETURN count(t) AS count",
    "MATCH (t:Tag) RETURN count(t) AS count",
    "MATCH (s:Source) RETURN count(s) AS count",
  ] as const;

  const results = await Promise.all(queries.map((q) => graph.query(q)));

  function extractCount(result: Awaited<ReturnType<typeof graph.query>>): number {
    if (result.hasNext()) {
      const record = result.next();
      return (record.get("count") as number) ?? 0;
    }
    return 0;
  }

  return {
    documents: extractCount(results[0]!),
    topics: extractCount(results[1]!),
    tags: extractCount(results[2]!),
    sources: extractCount(results[3]!),
  };
}

export async function createEntry(entry: {
  url: string;
  title: string;
  notes: string;
  tags: string[];
}): Promise<{ path: string }> {
  const graph = await getGraph();
  const now = new Date().toISOString();
  const slug = entry.title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  const path = `inbox/${slug}.md`;

  const cypher = `
    MERGE (d:Document {path: $path})
    SET d.title = $title,
        d.source_url = $url,
        d.source_type = 'manual',
        d.status = 'inbox',
        d.content = $notes,
        d.created_at = $now,
        d.updated_at = $now
    RETURN d.path AS path
  `;

  await graph.query(cypher, {
    params: {
      path,
      title: entry.title,
      url: entry.url,
      notes: entry.notes,
      now,
    },
  });

  for (const tagName of entry.tags) {
    const normalizedName = tagName.toLowerCase().trim();
    const tagCypher = `
      MERGE (t:Tag {normalized_name: $normalizedName})
      ON CREATE SET t.name = $tagName
      WITH t
      MATCH (d:Document {path: $path})
      MERGE (d)-[:TAGGED_WITH]->(t)
    `;
    await graph.query(tagCypher, {
      params: { normalizedName, tagName, path },
    });
  }

  return { path };
}

export async function getTopics(): Promise<Array<{ name: string; level: number }>> {
  const graph = await getGraph();

  const cypher = `
    MATCH (t:Topic)
    RETURN t.name AS name, t.level AS level
    ORDER BY t.level ASC, t.name ASC
  `;

  const result = await graph.query(cypher);
  const topics: Array<{ name: string; level: number }> = [];

  while (result.hasNext()) {
    const record = result.next();
    topics.push({
      name: (record.get("name") as string) ?? "",
      level: (record.get("level") as number) ?? 0,
    });
  }

  return topics;
}

export async function closeConnection(): Promise<void> {
  if (clientInstance) {
    await clientInstance.close();
    clientInstance = null;
  }
}
