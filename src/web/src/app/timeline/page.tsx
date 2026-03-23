"use client";

import { useCallback, useEffect, useState } from "react";

import { STATUS_LABELS } from "@/lib/constants";

interface TimelineDocument {
  path: string;
  title: string;
  summary: string;
  status: string;
  sourceType: string;
  sourceUrl: string;
  createdAt: string;
  updatedAt: string;
  paraCategory: string;
  topics: string[];
  tags: string[];
}

interface DateGroup {
  label: string;
  documents: TimelineDocument[];
}

function groupByDate(documents: TimelineDocument[]): DateGroup[] {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today.getTime() - 86_400_000);
  const weekAgo = new Date(today.getTime() - 7 * 86_400_000);
  const monthAgo = new Date(today.getTime() - 30 * 86_400_000);

  const groups: Record<string, TimelineDocument[]> = {
    Today: [],
    Yesterday: [],
    "This Week": [],
    "This Month": [],
    Older: [],
  };

  for (const doc of documents) {
    const created = new Date(doc.createdAt);
    if (isNaN(created.getTime())) {
      groups["Older"]!.push(doc);
    } else if (created >= today) {
      groups["Today"]!.push(doc);
    } else if (created >= yesterday) {
      groups["Yesterday"]!.push(doc);
    } else if (created >= weekAgo) {
      groups["This Week"]!.push(doc);
    } else if (created >= monthAgo) {
      groups["This Month"]!.push(doc);
    } else {
      groups["Older"]!.push(doc);
    }
  }

  return Object.entries(groups)
    .filter(([, docs]) => docs.length > 0)
    .map(([label, docs]) => ({ label, documents: docs }));
}

const SOURCE_BADGE_STYLES: Record<string, string> = {
  keepmd:
    "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
  obsidian_clipper:
    "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400",
  manual:
    "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300",
};

const SOURCE_LABELS: Record<string, string> = {
  keepmd: "keep.md",
  obsidian_clipper: "Obsidian",
  manual: "Manual",
};

function SourceBadge({ sourceType }: { sourceType: string }) {
  const style = SOURCE_BADGE_STYLES[sourceType] ?? SOURCE_BADGE_STYLES["manual"];
  const label = SOURCE_LABELS[sourceType] ?? sourceType;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${style}`}
    >
      {label}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    inbox: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
    processing: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
    published: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    archived: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400",
  };
  const style = colors[status] ?? colors["inbox"];
  const label = STATUS_LABELS[status] ?? status;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${style}`}
    >
      {label}
    </span>
  );
}

function TimelineEntry({ doc }: { doc: TimelineDocument }) {
  const [expanded, setExpanded] = useState(false);

  const formattedDate = doc.createdAt
    ? new Date(doc.createdAt).toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "Unknown date";

  const summarySnippet =
    doc.summary.length > 180 ? doc.summary.slice(0, 180) + "..." : doc.summary;

  return (
    <div className="group relative pl-8">
      {/* Timeline dot */}
      <div
        className="absolute left-0 top-2 h-3 w-3 rounded-full border-2 border-brand-500 bg-white dark:bg-gray-900"
        aria-hidden="true"
      />

      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        className="w-full rounded-lg border border-gray-200 bg-white p-4 text-left transition-colors hover:border-brand-300 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-brand-700 dark:hover:bg-gray-750"
        aria-expanded={expanded}
      >
        {/* Header row */}
        <div className="flex flex-wrap items-start justify-between gap-2">
          <h3 className="text-sm font-semibold leading-tight">{doc.title || "Untitled"}</h3>
          <div className="flex shrink-0 items-center gap-2">
            <SourceBadge sourceType={doc.sourceType} />
            <StatusBadge status={doc.status} />
          </div>
        </div>

        {/* Summary snippet */}
        {summarySnippet && (
          <p className="mt-1.5 text-sm text-gray-600 dark:text-gray-400">{summarySnippet}</p>
        )}

        {/* Topics and tags row */}
        {(doc.topics.length > 0 || doc.tags.length > 0) && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {doc.topics.map((topic) => (
              <span
                key={topic}
                className="inline-flex items-center rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400"
              >
                {topic}
              </span>
            ))}
            {doc.tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center rounded-md bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-900/20 dark:text-amber-400"
              >
                #{tag}
              </span>
            ))}
          </div>
        )}

        {/* Timestamp */}
        <p className="mt-2 text-xs text-gray-400 dark:text-gray-500">{formattedDate}</p>

        {/* Expanded details */}
        {expanded && (
          <div
            className="mt-3 space-y-2 border-t border-gray-100 pt-3 dark:border-gray-700"
            onClick={(e) => e.stopPropagation()}
            role="region"
            aria-label={`Details for ${doc.title}`}
          >
            {doc.summary && (
              <div>
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                  Summary
                </span>
                <p className="mt-0.5 text-sm text-gray-700 dark:text-gray-300">{doc.summary}</p>
              </div>
            )}
            {doc.sourceUrl && (
              <div>
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                  Source
                </span>
                <p className="mt-0.5">
                  <a
                    href={doc.sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-brand-600 underline decoration-brand-300 hover:text-brand-700 dark:text-brand-400 dark:decoration-brand-700 dark:hover:text-brand-300"
                  >
                    {doc.sourceUrl}
                  </a>
                </p>
              </div>
            )}
            <div className="flex gap-4 text-xs text-gray-500 dark:text-gray-400">
              <span>Path: {doc.path}</span>
              {doc.paraCategory && <span>Category: {doc.paraCategory}</span>}
            </div>
          </div>
        )}
      </button>
    </div>
  );
}

export default function TimelinePage() {
  const [documents, setDocuments] = useState<TimelineDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [limit, setLimit] = useState(50);

  const fetchTimeline = useCallback(async (docLimit: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/timeline?limit=${docLimit}`);
      if (!response.ok) {
        const data = (await response.json()) as { error?: string };
        throw new Error(data.error ?? `Request failed with status ${response.status}`);
      }
      const data = (await response.json()) as { documents: TimelineDocument[] };
      setDocuments(data.documents);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load timeline";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchTimeline(limit);
  }, [fetchTimeline, limit]);

  const groups = groupByDate(documents);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Timeline</h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Your knowledge graph entries in chronological order.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label htmlFor="timeline-limit" className="text-xs text-gray-500 dark:text-gray-400">
            Show
          </label>
          <select
            id="timeline-limit"
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="rounded-lg border border-gray-300 bg-white px-2 py-1.5 text-sm dark:border-gray-700 dark:bg-gray-800"
          >
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={200}>200</option>
          </select>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div
          className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400"
          role="alert"
        >
          {error}
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
          <span className="sr-only">Loading timeline...</span>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && documents.length === 0 && (
        <div className="rounded-lg border border-dashed border-gray-300 p-12 text-center dark:border-gray-700">
          <svg
            className="mx-auto h-10 w-10 text-gray-400 dark:text-gray-600"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h3 className="mt-3 text-sm font-semibold">No entries yet</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Add your first entry to see it on the timeline.
          </p>
        </div>
      )}

      {/* Timeline groups */}
      {!loading &&
        groups.map((group) => (
          <section key={group.label} aria-label={`${group.label} entries`}>
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
              {group.label}
              <span className="ml-2 text-gray-400 dark:text-gray-500">
                ({group.documents.length})
              </span>
            </h3>
            <div className="relative space-y-3">
              {/* Vertical line */}
              <div
                className="absolute bottom-0 left-[5px] top-0 w-px bg-gray-200 dark:bg-gray-700"
                aria-hidden="true"
              />
              {group.documents.map((doc) => (
                <TimelineEntry key={doc.path} doc={doc} />
              ))}
            </div>
          </section>
        ))}
    </div>
  );
}
