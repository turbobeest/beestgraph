"use client";

import type { Core, ElementDefinition, EventObject } from "cytoscape";
import { useCallback, useEffect, useRef, useState } from "react";

import { NODE_COLORS } from "@/lib/constants";

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

interface GraphExplorerProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  searchHighlight?: string;
  onNodeClick?: (nodeId: string, label: string) => void;
}

function toElements(nodes: GraphNode[], edges: GraphEdge[]): ElementDefinition[] {
  const elements: ElementDefinition[] = [];

  for (const node of nodes) {
    const displayName =
      (node.properties["title"] as string) ??
      (node.properties["name"] as string) ??
      node.id;

    elements.push({
      data: {
        id: node.id,
        label: displayName,
        nodeType: node.label,
        ...node.properties,
      },
    });
  }

  for (let i = 0; i < edges.length; i++) {
    const edge = edges[i]!;
    elements.push({
      data: {
        id: `edge-${String(i)}`,
        source: edge.source,
        target: edge.target,
        label: edge.relationship,
        ...edge.properties,
      },
    });
  }

  return elements;
}

export default function GraphExplorer({
  nodes,
  edges,
  searchHighlight,
  onNodeClick,
}: GraphExplorerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    let cy: Core;

    async function init() {
      const cytoscape = (await import("cytoscape")).default;

      cy = cytoscape({
        container: containerRef.current,
        elements: toElements(nodes, edges),
        style: [
          {
            selector: "node",
            style: {
              label: "data(label)",
              "text-valign": "bottom",
              "text-halign": "center",
              "font-size": "11px",
              "text-margin-y": 8,
              "text-max-width": "100px",
              "text-wrap": "ellipsis",
              color: "#9ca3af",
              "background-color": (ele) => {
                const nodeType = ele.data("nodeType") as string;
                return NODE_COLORS[nodeType] ?? "#6b7280";
              },
              width: 30,
              height: 30,
              "border-width": 2,
              "border-color": "transparent",
            },
          },
          {
            selector: "node:selected",
            style: {
              "border-color": "#d4a017",
              "border-width": 3,
              width: 40,
              height: 40,
            },
          },
          {
            selector: "node.highlighted",
            style: {
              "border-color": "#ef4444",
              "border-width": 3,
              width: 38,
              height: 38,
            },
          },
          {
            selector: "edge",
            style: {
              width: 1.5,
              "line-color": "#4b5563",
              "target-arrow-color": "#4b5563",
              "target-arrow-shape": "triangle",
              "curve-style": "bezier",
              label: "data(label)",
              "font-size": "9px",
              "text-rotation": "autorotate",
              color: "#6b7280",
              "text-opacity": 0.7,
            },
          },
        ],
        layout: {
          name: "cose",
          animate: true,
          animationDuration: 500,
          nodeRepulsion: () => 8000,
          idealEdgeLength: () => 120,
          gravity: 0.25,
        },
        minZoom: 0.2,
        maxZoom: 5,
      });

      cyRef.current = cy;

      cy.on("tap", "node", (evt: EventObject) => {
        const nodeData = evt.target.data() as Record<string, unknown>;
        const nodeId = nodeData["id"] as string;
        const nodeType = nodeData["nodeType"] as string;
        setSelectedNode({
          id: nodeId,
          label: nodeType,
          properties: nodeData as Record<string, string | number | boolean | null>,
        });
        onNodeClick?.(nodeId, nodeType);
      });

      cy.on("tap", (evt: EventObject) => {
        if (evt.target === cy) {
          setSelectedNode(null);
        }
      });
    }

    void init();

    return () => {
      cy?.destroy();
      cyRef.current = null;
    };
    // Intentionally only run on mount/remount when data changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, edges]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    cy.nodes().removeClass("highlighted");

    if (searchHighlight) {
      const term = searchHighlight.toLowerCase();
      cy.nodes().forEach((node) => {
        const label = (node.data("label") as string)?.toLowerCase() ?? "";
        if (label.includes(term)) {
          node.addClass("highlighted");
        }
      });
    }
  }, [searchHighlight]);

  const handleFit = useCallback(() => {
    cyRef.current?.fit(undefined, 50);
  }, []);

  const handleRelayout = useCallback(() => {
    cyRef.current?.layout({
      name: "cose",
      animate: true,
      animationDuration: 500,
      nodeRepulsion: () => 8000,
      idealEdgeLength: () => 120,
      gravity: 0.25,
    }).run();
  }, []);

  return (
    <div className="flex h-full flex-col">
      {/* Toolbar */}
      <div className="flex items-center gap-2 border-b border-gray-200 px-4 py-2 dark:border-gray-700">
        <button
          type="button"
          onClick={handleFit}
          className="rounded-md bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
          aria-label="Fit graph to viewport"
        >
          Fit view
        </button>
        <button
          type="button"
          onClick={handleRelayout}
          className="rounded-md bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
          aria-label="Recalculate graph layout"
        >
          Re-layout
        </button>
        <div className="ml-auto flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
          <span>{nodes.length} nodes</span>
          <span>{edges.length} edges</span>
        </div>
      </div>

      {/* Graph canvas */}
      <div className="relative flex-1">
        <div ref={containerRef} className="cytoscape-container absolute inset-0" />
      </div>

      {/* Node detail panel */}
      {selectedNode && (
        <div className="border-t border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800/50">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">
              <span
                className="mr-2 inline-block h-3 w-3 rounded-full"
                style={{ backgroundColor: NODE_COLORS[selectedNode.label] ?? "#6b7280" }}
                aria-hidden="true"
              />
              {selectedNode.label}
            </h3>
            <button
              type="button"
              onClick={() => setSelectedNode(null)}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              aria-label="Close node details"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
            {Object.entries(selectedNode.properties)
              .filter(([key]) => !["id", "nodeType"].includes(key))
              .map(([key, val]) => (
                <div key={key} className="contents">
                  <dt className="font-medium text-gray-500 dark:text-gray-400">{key}</dt>
                  <dd className="truncate text-gray-700 dark:text-gray-300">
                    {val !== null && val !== undefined ? String(val) : "-"}
                  </dd>
                </div>
              ))}
          </dl>
        </div>
      )}
    </div>
  );
}
