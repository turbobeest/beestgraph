"use client";

import { useCallback, useEffect, useState } from "react";

import EntryCard from "@/components/EntryCard";
import SearchBar from "@/components/SearchBar";
import StatsCard from "@/components/StatsCard";

interface DocumentResult {
  path: string;
  title: string;
  summary: string;
  status: string;
  sourceType: string;
  sourceUrl: string;
  createdAt: string;
  updatedAt: string;
}

interface Stats {
  documents: number;
  topics: number;
  tags: number;
  sources: number;
}

export default function DashboardPage() {
  const [documents, setDocuments] = useState<DocumentResult[]>([]);
  const [stats, setStats] = useState<Stats>({ documents: 0, topics: 0, tags: 0, sources: 0 });
  const [loading, setLoading] = useState(true);
  const [searchResults, setSearchResults] = useState<DocumentResult[] | null>(null);

  useEffect(() => {
    async function fetchDashboard() {
      try {
        const [docsRes, statsRes] = await Promise.all([
          fetch("/api/search?recent=true"),
          fetch("/api/stats"),
        ]);

        if (docsRes.ok) {
          const data = (await docsRes.json()) as { documents: DocumentResult[] };
          setDocuments(data.documents ?? []);
        }

        if (statsRes.ok) {
          const data = (await statsRes.json()) as Stats;
          setStats(data);
        }
      } catch (err) {
        console.error("Dashboard fetch error:", err);
      } finally {
        setLoading(false);
      }
    }

    void fetchDashboard();
  }, []);

  const handleSearch = useCallback(async (query: string) => {
    if (!query.trim()) {
      setSearchResults(null);
      return;
    }

    try {
      const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
      if (response.ok) {
        const data = (await response.json()) as { documents: DocumentResult[] };
        setSearchResults(data.documents ?? []);
      }
    } catch (err) {
      console.error("Search error:", err);
    }
  }, []);

  const displayDocs = searchResults ?? documents;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Dashboard</h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Your knowledge graph at a glance.
        </p>
      </div>

      <SearchBar onSearch={handleSearch} />

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatsCard label="Documents" value={stats.documents} icon="document" />
        <StatsCard label="Topics" value={stats.topics} icon="topic" />
        <StatsCard label="Tags" value={stats.tags} icon="tag" />
        <StatsCard label="Sources" value={stats.sources} icon="source" />
      </div>

      {/* Document list */}
      <section>
        <h3 className="mb-3 text-lg font-semibold">
          {searchResults ? "Search results" : "Recent documents"}
        </h3>

        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={`skeleton-${String(i)}`}
                className="h-24 animate-pulse rounded-xl bg-gray-200 dark:bg-gray-700"
              />
            ))}
          </div>
        ) : displayDocs.length === 0 ? (
          <p className="rounded-xl border border-dashed border-gray-300 p-8 text-center text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
            {searchResults ? "No matching documents found." : "No documents yet. Add your first entry."}
          </p>
        ) : (
          <div className="space-y-3">
            {displayDocs.map((doc) => (
              <EntryCard
                key={doc.path}
                title={doc.title}
                summary={doc.summary}
                status={doc.status}
                sourceType={doc.sourceType}
                sourceUrl={doc.sourceUrl}
                createdAt={doc.createdAt}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
