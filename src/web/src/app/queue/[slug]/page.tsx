"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import type { QueueItem, QueueItemDetail } from "@/lib/queue";
import { CONTENT_TYPES, TOPICS, CONFIDENCE_OPTIONS } from "@/lib/queue";

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ConfidenceSegment({
  value,
  onChange,
}: {
  value: number | null;
  onChange: (v: number) => void;
}) {
  return (
    <div className="flex rounded-lg border border-gray-300 dark:border-gray-600" role="radiogroup" aria-label="Confidence">
      {CONFIDENCE_OPTIONS.map((opt) => (
        <button
          key={opt.value}
          type="button"
          role="radio"
          aria-checked={value === opt.value}
          onClick={() => onChange(opt.value)}
          className={`min-h-[44px] flex-1 px-3 py-2 text-sm font-medium transition-colors first:rounded-l-lg last:rounded-r-lg ${
            value === opt.value
              ? opt.value >= 0.7
                ? "bg-green-600 text-white"
                : opt.value >= 0.4
                  ? "bg-yellow-600 text-white"
                  : "bg-red-600 text-white"
              : "bg-white text-gray-700 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          }`}
        >
          {opt.label} ({opt.value})
        </button>
      ))}
    </div>
  );
}

function TagChips({
  tags,
  onRemove,
  onAdd,
}: {
  tags: string[];
  onRemove: (tag: string) => void;
  onAdd: (tag: string) => void;
}) {
  const [input, setInput] = useState("");

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && input.trim()) {
      e.preventDefault();
      onAdd(input.trim());
      setInput("");
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1.5">
        {tags.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-sm dark:bg-gray-700"
          >
            {tag}
            <button
              type="button"
              onClick={() => onRemove(tag)}
              className="ml-0.5 inline-flex h-4 w-4 items-center justify-center rounded-full text-gray-500 hover:bg-gray-200 hover:text-gray-700 dark:hover:bg-gray-600 dark:hover:text-gray-200"
              aria-label={`Remove tag ${tag}`}
            >
              &times;
            </button>
          </span>
        ))}
      </div>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Add tag..."
        className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
        aria-label="Add a tag"
      />
    </div>
  );
}

function SecurityBadge({ findings }: { findings: string }) {
  if (!findings) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-1 text-xs font-medium text-green-800 dark:bg-green-900/30 dark:text-green-400">
        &#x2713; Security scan passed
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-orange-100 px-2.5 py-1 text-xs font-medium text-orange-800 dark:bg-orange-900/30 dark:text-orange-400">
      &#x26a0; {findings}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Main page component
// ---------------------------------------------------------------------------

export default function QueueItemPage() {
  const routeParams = useParams();
  const router = useRouter();
  const slug = typeof routeParams.slug === "string" ? routeParams.slug : "";

  const [item, setItem] = useState<QueueItemDetail | null>(null);
  const [allSlugs, setAllSlugs] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState("");
  const [error, setError] = useState("");

  // Editable state
  const [summary, setSummary] = useState("");
  const [type, setType] = useState("");
  const [topic, setTopic] = useState("");
  const [confidence, setConfidence] = useState<number | null>(null);
  const [tags, setTags] = useState<string[]>([]);

  // Fetch list for prev/next navigation
  useEffect(() => {
    async function fetchList() {
      try {
        const res = await fetch("/api/queue");
        if (res.ok) {
          const data = (await res.json()) as { items: QueueItem[] };
          setAllSlugs(data.items.map((i) => i.slug));
        }
      } catch {
        // Non-critical
      }
    }
    void fetchList();
  }, []);

  // Fetch item detail
  useEffect(() => {
    if (!slug) return;
    async function fetchItem() {
      setLoading(true);
      setError("");
      try {
        const res = await fetch(`/api/queue/${slug}`);
        if (res.status === 404) {
          setError("Item not found. It may have been approved or rejected.");
          setItem(null);
          return;
        }
        if (!res.ok) throw new Error(`HTTP ${String(res.status)}`);
        const data = (await res.json()) as QueueItemDetail;
        setItem(data);
        setSummary(data.summary);
        setType(data.type);
        setTopic(data.topic);
        setConfidence(data.confidence);
        setTags([...data.tags]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load item");
      } finally {
        setLoading(false);
      }
    }
    void fetchItem();
  }, [slug]);

  // Navigation
  const currentIndex = allSlugs.indexOf(slug);
  const prevSlug = currentIndex > 0 ? allSlugs[currentIndex - 1] : null;
  const nextSlug = currentIndex < allSlugs.length - 1 ? allSlugs[currentIndex + 1] : null;
  const totalCount = allSlugs.length;
  const currentPosition = currentIndex >= 0 ? currentIndex + 1 : 0;

  // Navigate to next item (or back to queue list if none)
  const goNext = useCallback(() => {
    if (nextSlug) {
      router.push(`/queue/${nextSlug}`);
    } else if (prevSlug) {
      router.push(`/queue/${prevSlug}`);
    } else {
      router.push("/queue");
    }
  }, [nextSlug, prevSlug, router]);

  // Save changes
  const saveChanges = useCallback(async () => {
    if (!item) return;
    try {
      const res = await fetch(`/api/queue/${slug}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type, topic, tags, confidence, summary }),
      });
      if (!res.ok) throw new Error("Save failed");
    } catch (err) {
      console.error("Save error:", err);
    }
  }, [item, slug, type, topic, tags, confidence, summary]);

  // Actions
  const handleApprove = useCallback(
    async (contentStage: "fleeting" | "evergreen") => {
      if (!item) return;
      setActionLoading(contentStage);
      // Save any pending changes first
      await saveChanges();
      try {
        const res = await fetch(`/api/queue/${slug}/approve`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content_stage: contentStage }),
        });
        if (!res.ok) throw new Error("Approve failed");
        goNext();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Approve failed");
      } finally {
        setActionLoading("");
      }
    },
    [item, slug, saveChanges, goNext],
  );

  const handleReject = useCallback(async () => {
    if (!item) return;
    setActionLoading("reject");
    try {
      const res = await fetch(`/api/queue/${slug}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!res.ok) throw new Error("Reject failed");
      goNext();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reject failed");
    } finally {
      setActionLoading("");
    }
  }, [item, slug, goNext]);

  const handleLater = useCallback(() => {
    goNext();
  }, [goNext]);

  // Tag operations
  const handleRemoveTag = useCallback((tag: string) => {
    setTags((prev) => prev.filter((t) => t !== tag));
  }, []);

  const handleAddTag = useCallback((tag: string) => {
    setTags((prev) => (prev.includes(tag) ? prev : [...prev, tag]));
  }, []);

  // Loading state
  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        <div className="h-64 animate-pulse rounded-xl bg-gray-200 dark:bg-gray-700" />
      </div>
    );
  }

  // Error / not found
  if (error && !item) {
    return (
      <div className="space-y-4">
        <Link
          href="/queue"
          className="inline-flex min-h-[44px] items-center gap-1 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          aria-label="Back to queue"
        >
          &larr; Queue
        </Link>
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
          {error}
        </div>
      </div>
    );
  }

  if (!item) return null;

  return (
    <div className="pb-32">
      {/* Top navigation */}
      <div className="mb-4 flex items-center justify-between">
        <Link
          href="/queue"
          className="inline-flex min-h-[44px] items-center gap-1 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          aria-label="Back to queue"
        >
          &larr; Queue
        </Link>
        <div className="flex items-center gap-3">
          {prevSlug ? (
            <Link
              href={`/queue/${prevSlug}`}
              className="inline-flex min-h-[44px] items-center rounded-lg px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
              aria-label="Previous item"
            >
              &larr; Prev
            </Link>
          ) : (
            <span className="px-3 py-2 text-sm text-gray-300 dark:text-gray-600">&larr; Prev</span>
          )}
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {currentPosition} of {totalCount}
          </span>
          {nextSlug ? (
            <Link
              href={`/queue/${nextSlug}`}
              className="inline-flex min-h-[44px] items-center rounded-lg px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
              aria-label="Next item"
            >
              Next &rarr;
            </Link>
          ) : (
            <span className="px-3 py-2 text-sm text-gray-300 dark:text-gray-600">Next &rarr;</span>
          )}
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Title */}
      <h1 className="text-2xl font-bold leading-tight">{item.title || "Untitled"}</h1>

      {/* Status bar */}
      <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
        <span>{type || "untyped"}</span>
        <span>&middot;</span>
        <span>{topic || "no topic"}</span>
        {confidence !== null && (
          <>
            <span>&middot;</span>
            <span>confidence: {confidence}</span>
          </>
        )}
        {item.sourceUrl && (
          <>
            <span>&middot;</span>
            <a
              href={item.sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-brand-600 hover:underline dark:text-brand-400"
            >
              Source
            </a>
          </>
        )}
      </div>

      {/* Security badge */}
      <div className="mt-3">
        <SecurityBadge findings={item.securityFindings} />
      </div>

      {/* Summary (editable) */}
      <div className="mt-6">
        <label htmlFor="summary" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
          Summary
        </label>
        <textarea
          id="summary"
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          rows={3}
          className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
        />
      </div>

      {/* Content preview */}
      <div className="mt-6">
        <h3 className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Content</h3>
        <div className="max-h-64 overflow-y-auto rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900">
          <pre className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300">
            {item.content || "(empty)"}
          </pre>
        </div>
      </div>

      {/* Tags */}
      <div className="mt-6">
        <h3 className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Tags</h3>
        <TagChips tags={tags} onRemove={handleRemoveTag} onAdd={handleAddTag} />
      </div>

      {/* Type selector */}
      <div className="mt-6">
        <label htmlFor="type" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
          Type
        </label>
        <select
          id="type"
          value={type}
          onChange={(e) => setType(e.target.value)}
          className="min-h-[44px] w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
        >
          <option value="">Select type...</option>
          {CONTENT_TYPES.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      {/* Topic selector */}
      <div className="mt-6">
        <label htmlFor="topic" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
          Topic
        </label>
        <select
          id="topic"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          className="min-h-[44px] w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
        >
          <option value="">Select topic...</option>
          {TOPICS.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      {/* Confidence toggle */}
      <div className="mt-6">
        <h3 className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Confidence</h3>
        <ConfidenceSegment value={confidence} onChange={setConfidence} />
      </div>

      {/* Sticky action buttons */}
      <div className="fixed bottom-0 left-0 right-0 border-t border-gray-200 bg-white/95 px-4 py-3 backdrop-blur-sm dark:border-gray-700 dark:bg-gray-900/95 md:left-64">
        <div className="mx-auto flex max-w-7xl items-center gap-2">
          {/* Approve as fleeting — primary */}
          <button
            type="button"
            onClick={() => void handleApprove("fleeting")}
            disabled={actionLoading !== ""}
            className="min-h-[44px] flex-1 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-brand-700 disabled:opacity-50"
          >
            {actionLoading === "fleeting" ? "..." : "Approve"}
          </button>

          {/* Approve as evergreen — secondary */}
          <button
            type="button"
            onClick={() => void handleApprove("evergreen")}
            disabled={actionLoading !== ""}
            className="min-h-[44px] rounded-lg border border-brand-600 bg-white px-4 py-2.5 text-sm font-semibold text-brand-600 transition-colors hover:bg-brand-50 disabled:opacity-50 dark:bg-gray-800 dark:text-brand-400 dark:hover:bg-gray-700"
          >
            {actionLoading === "evergreen" ? "..." : "Evergreen"}
          </button>

          {/* Reject — danger */}
          <button
            type="button"
            onClick={() => void handleReject()}
            disabled={actionLoading !== ""}
            className="min-h-[44px] rounded-lg bg-red-100 px-3 py-2.5 text-sm font-medium text-red-700 transition-colors hover:bg-red-200 disabled:opacity-50 dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-900/50"
          >
            {actionLoading === "reject" ? "..." : "Reject"}
          </button>

          {/* Later — gray */}
          <button
            type="button"
            onClick={handleLater}
            disabled={actionLoading !== ""}
            className="min-h-[44px] rounded-lg bg-gray-100 px-3 py-2.5 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-200 disabled:opacity-50 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700"
          >
            Later
          </button>
        </div>
      </div>
    </div>
  );
}
