"use client";

import { useCallback, useEffect, useState } from "react";

import GraphExplorer from "@/components/GraphExplorer";
import SearchBar from "@/components/SearchBar";
import TopicTree from "@/components/TopicTree";

interface GraphNode {
  id: string;
  label: string;
  properties: Record<string, string | number | boolean | null>;
}

interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
  properties: Record<string, string | number | boolean | null>;
}

interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export default function GraphPage() {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const fetchGraph = useCallback(async (topic: string | null, search: string) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (topic) params.set("topic", topic);
      if (search) params.set("search", search);

      const response = await fetch(`/api/graph?${params.toString()}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch graph: ${response.status}`);
      }

      const data = (await response.json()) as GraphResponse;
      setNodes(data.nodes ?? []);
      setEdges(data.edges ?? []);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load graph data";
      setError(message);
      console.error("Graph fetch error:", message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchGraph(selectedTopic, searchTerm);
  }, [fetchGraph, selectedTopic, searchTerm]);

  const handleTopicSelect = useCallback((topic: string | null) => {
    setSelectedTopic(topic);
  }, []);

  const handleSearch = useCallback((query: string) => {
    setSearchTerm(query);
  }, []);

  const handleNodeClick = useCallback(
    (_nodeId: string, _label: string) => {
      // Future: expand node connections or navigate to detail view
    },
    [],
  );

  return (
    <div className="flex h-[calc(100vh-theme(spacing.6)*2)] flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Graph Explorer</h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Visualize and explore your knowledge graph.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setSidebarOpen((prev) => !prev)}
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium transition-colors hover:bg-gray-100 dark:border-gray-600 dark:hover:bg-gray-800"
          aria-label={sidebarOpen ? "Hide topic filter" : "Show topic filter"}
        >
          {sidebarOpen ? "Hide filters" : "Show filters"}
        </button>
      </div>

      <SearchBar onSearch={handleSearch} placeholder="Search graph nodes..." />

      <div className="flex min-h-0 flex-1 gap-4">
        {/* Topic filter sidebar */}
        {sidebarOpen && (
          <aside className="w-56 shrink-0 overflow-y-auto rounded-xl border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-800">
            <h3 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
              Topics
            </h3>
            <TopicTree onSelectTopic={handleTopicSelect} selectedTopic={selectedTopic} />
          </aside>
        )}

        {/* Graph area */}
        <div className="min-h-0 flex-1 overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
          {loading ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-sm text-gray-500 dark:text-gray-400">Loading graph...</div>
            </div>
          ) : error ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <p className="text-sm text-red-500">{error}</p>
                <button
                  type="button"
                  onClick={() => void fetchGraph(selectedTopic, searchTerm)}
                  className="mt-2 text-sm text-brand-600 hover:text-brand-700 dark:text-brand-400"
                >
                  Retry
                </button>
              </div>
            </div>
          ) : nodes.length === 0 ? (
            <div className="flex h-full items-center justify-center">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                No graph data available. Add some documents first.
              </p>
            </div>
          ) : (
            <GraphExplorer
              nodes={nodes}
              edges={edges}
              searchHighlight={searchTerm}
              onNodeClick={handleNodeClick}
            />
          )}
        </div>
      </div>
    </div>
  );
}
