export const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: "home" },
  { href: "/timeline", label: "Timeline", icon: "timeline" },
  { href: "/graph", label: "Graph", icon: "graph" },
  { href: "/entry", label: "New Entry", icon: "plus" },
] as const;

export const NODE_COLORS: Record<string, string> = {
  Document: "#3b82f6",
  Topic: "#10b981",
  Tag: "#f59e0b",
  Person: "#ef4444",
  Concept: "#8b5cf6",
  Source: "#6366f1",
  Project: "#ec4899",
};

export const STATUS_LABELS: Record<string, string> = {
  inbox: "Inbox",
  processing: "Processing",
  published: "Published",
  archived: "Archived",
};

export const DEBOUNCE_MS = 300;
