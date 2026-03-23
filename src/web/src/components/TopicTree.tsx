"use client";

import { useCallback, useEffect, useState } from "react";

interface TopicNode {
  name: string;
  level: number;
}

interface TopicTreeProps {
  onSelectTopic: (topic: string | null) => void;
  selectedTopic: string | null;
}

export default function TopicTree({ onSelectTopic, selectedTopic }: TopicTreeProps) {
  const [topics, setTopics] = useState<TopicNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchTopics() {
      try {
        const response = await fetch("/api/graph?topicsOnly=true");
        if (!response.ok) {
          throw new Error(`Failed to fetch topics: ${response.status}`);
        }
        const data = (await response.json()) as { topics: TopicNode[] };
        setTopics(data.topics ?? []);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to load topics";
        setError(message);
        console.error("TopicTree fetch error:", message);
      } finally {
        setLoading(false);
      }
    }

    void fetchTopics();
  }, []);

  const handleClear = useCallback(() => {
    onSelectTopic(null);
  }, [onSelectTopic]);

  if (loading) {
    return (
      <div className="space-y-2 p-2" aria-label="Loading topics">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={`skeleton-${String(i)}`}
            className="h-8 animate-pulse rounded bg-gray-200 dark:bg-gray-700"
          />
        ))}
      </div>
    );
  }

  if (error) {
    return <p className="p-2 text-sm text-red-500">{error}</p>;
  }

  if (topics.length === 0) {
    return <p className="p-2 text-sm text-gray-500 dark:text-gray-400">No topics found.</p>;
  }

  return (
    <div className="space-y-0.5">
      <button
        type="button"
        onClick={handleClear}
        className={`w-full rounded-lg px-3 py-2 text-left text-sm font-medium transition-colors ${
          selectedTopic === null
            ? "bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400"
            : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
        }`}
        aria-pressed={selectedTopic === null}
      >
        All topics
      </button>
      {topics.map((topic) => (
        <button
          key={topic.name}
          type="button"
          onClick={() => onSelectTopic(topic.name)}
          className={`w-full rounded-lg px-3 py-2 text-left text-sm transition-colors ${
            selectedTopic === topic.name
              ? "bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400"
              : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
          }`}
          style={{ paddingLeft: `${(topic.level + 1) * 12}px` }}
          aria-pressed={selectedTopic === topic.name}
        >
          {topic.name}
        </button>
      ))}
    </div>
  );
}
