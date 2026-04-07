"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import type { QueueItem } from "@/lib/queue";

function ConfidenceBadge({ confidence }: { confidence: number | null }) {
  if (confidence === null) return null;
  const label = confidence >= 0.7 ? "High" : confidence >= 0.4 ? "Med" : "Low";
  const colors =
    confidence >= 0.7
      ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
      : confidence >= 0.4
        ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400"
        : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400";
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${colors}`}>
      {label} ({confidence})
    </span>
  );
}

function TypeBadge({ type }: { type: string }) {
  if (!type) return null;
  const colorMap: Record<string, string> = {
    article: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
    reference: "bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-400",
    tool: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    film: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
    note: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
    bookmark: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400",
    thread: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
    repo: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400",
  };
  const colors = colorMap[type] ?? "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400";
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${colors}`}>
      {type}
    </span>
  );
}

function SecurityBadge({ findings }: { findings: string }) {
  if (!findings) {
    return (
      <span
        className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800 dark:bg-green-900/30 dark:text-green-400"
        title="Security scan passed"
      >
        &#x2713; Scan OK
      </span>
    );
  }
  return (
    <span
      className="inline-flex items-center rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-800 dark:bg-orange-900/30 dark:text-orange-400"
      title={findings}
    >
      &#x26a0; Flag
    </span>
  );
}

export default function QueuePage() {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchQueue = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/queue");
      if (!res.ok) throw new Error(`HTTP ${String(res.status)}`);
      const data = (await res.json()) as { items: QueueItem[]; count: number };
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load queue");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchQueue();
  }, [fetchQueue]);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold tracking-tight">Queue</h2>
          {items.length > 0 && (
            <span className="inline-flex items-center justify-center rounded-full bg-brand-500 px-2.5 py-0.5 text-xs font-bold text-white">
              {items.length}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={() => void fetchQueue()}
          disabled={loading}
          className="inline-flex min-h-[44px] items-center gap-2 rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-200 disabled:opacity-50 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          aria-label="Refresh queue"
        >
          <svg
            className={`h-4 w-4 ${loading ? "animate-spin" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182"
            />
          </svg>
          Refresh
        </button>
      </div>

      <p className="text-sm text-gray-500 dark:text-gray-400">
        Items awaiting review. Tap to open.
      </p>

      {/* Error state */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Loading state */}
      {loading && !items.length ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={`skeleton-${String(i)}`}
              className="h-20 animate-pulse rounded-xl bg-gray-200 dark:bg-gray-700"
            />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 p-12 text-center dark:border-gray-700">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1}
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="mt-3 text-sm font-medium text-gray-500 dark:text-gray-400">
            Queue is empty
          </p>
          <p className="mt-1 text-xs text-gray-400 dark:text-gray-500">
            New captures will appear here for review.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {items.map((item, index) => (
            <Link
              key={item.slug}
              href={`/queue/${item.slug}`}
              className="block min-h-[44px] rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition-all hover:shadow-md active:scale-[0.99] dark:border-gray-700 dark:bg-gray-800"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <h3 className="truncate text-base font-semibold leading-tight">
                    {item.title || "Untitled"}
                  </h3>
                  <div className="mt-1.5 flex flex-wrap items-center gap-2">
                    <TypeBadge type={item.type} />
                    <ConfidenceBadge confidence={item.confidence} />
                    {item.topic && (
                      <span className="text-xs text-gray-500 dark:text-gray-400">{item.topic}</span>
                    )}
                    <SecurityBadge findings={item.securityFindings} />
                  </div>
                  {item.summary && (
                    <p className="mt-1.5 line-clamp-1 text-sm text-gray-500 dark:text-gray-400">
                      {item.summary}
                    </p>
                  )}
                </div>
                <span className="shrink-0 text-xs text-gray-400 dark:text-gray-500">
                  {index + 1}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
