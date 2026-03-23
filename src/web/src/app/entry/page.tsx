"use client";

import { useCallback, useState } from "react";

interface FormState {
  url: string;
  title: string;
  notes: string;
  tagInput: string;
  tags: string[];
}

const INITIAL_FORM: FormState = {
  url: "",
  title: "",
  notes: "",
  tagInput: "",
  tags: [],
};

export default function EntryPage() {
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);

  const handleFieldChange = useCallback(
    (field: keyof Pick<FormState, "url" | "title" | "notes" | "tagInput">) =>
      (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        setForm((prev) => ({ ...prev, [field]: e.target.value }));
      },
    [],
  );

  const addTag = useCallback(() => {
    const tag = form.tagInput.trim();
    if (tag && !form.tags.includes(tag)) {
      setForm((prev) => ({
        ...prev,
        tags: [...prev.tags, tag],
        tagInput: "",
      }));
    }
  }, [form.tagInput, form.tags]);

  const handleTagKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        e.preventDefault();
        addTag();
      }
    },
    [addTag],
  );

  const removeTag = useCallback((tagToRemove: string) => {
    setForm((prev) => ({
      ...prev,
      tags: prev.tags.filter((t) => t !== tagToRemove),
    }));
  }, []);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setSubmitting(true);
      setResult(null);

      try {
        const response = await fetch("/api/entry", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            url: form.url,
            title: form.title,
            notes: form.notes,
            tags: form.tags,
          }),
        });

        if (!response.ok) {
          const errorData = (await response.json()) as { error?: string };
          throw new Error(errorData.error ?? `Request failed with status ${response.status}`);
        }

        const data = (await response.json()) as { path: string };
        setResult({ success: true, message: `Entry created at ${data.path}` });
        setForm(INITIAL_FORM);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to create entry";
        setResult({ success: false, message });
      } finally {
        setSubmitting(false);
      }
    },
    [form],
  );

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">New Entry</h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Add a new document to your knowledge graph.
        </p>
      </div>

      {result && (
        <div
          className={`rounded-lg border p-4 text-sm ${
            result.success
              ? "border-green-200 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-900/20 dark:text-green-400"
              : "border-red-200 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400"
          }`}
          role="alert"
        >
          {result.message}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* URL */}
        <div>
          <label htmlFor="entry-url" className="block text-sm font-medium">
            URL
          </label>
          <input
            id="entry-url"
            type="url"
            value={form.url}
            onChange={handleFieldChange("url")}
            placeholder="https://example.com/article"
            className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm placeholder-gray-400 transition-colors focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-gray-700 dark:bg-gray-800 dark:placeholder-gray-500"
          />
        </div>

        {/* Title */}
        <div>
          <label htmlFor="entry-title" className="block text-sm font-medium">
            Title <span className="text-red-500">*</span>
          </label>
          <input
            id="entry-title"
            type="text"
            value={form.title}
            onChange={handleFieldChange("title")}
            placeholder="Article title or note name"
            required
            className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm placeholder-gray-400 transition-colors focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-gray-700 dark:bg-gray-800 dark:placeholder-gray-500"
          />
        </div>

        {/* Notes */}
        <div>
          <label htmlFor="entry-notes" className="block text-sm font-medium">
            Notes
          </label>
          <textarea
            id="entry-notes"
            value={form.notes}
            onChange={handleFieldChange("notes")}
            placeholder="Your notes, highlights, or the full article content..."
            rows={8}
            className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm placeholder-gray-400 transition-colors focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-gray-700 dark:bg-gray-800 dark:placeholder-gray-500"
          />
        </div>

        {/* Tags */}
        <div>
          <label htmlFor="entry-tags" className="block text-sm font-medium">
            Tags
          </label>
          <div className="mt-1 flex gap-2">
            <input
              id="entry-tags"
              type="text"
              value={form.tagInput}
              onChange={handleFieldChange("tagInput")}
              onKeyDown={handleTagKeyDown}
              placeholder="Add a tag and press Enter"
              className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm placeholder-gray-400 transition-colors focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-gray-700 dark:bg-gray-800 dark:placeholder-gray-500"
            />
            <button
              type="button"
              onClick={addTag}
              className="rounded-lg bg-gray-100 px-4 py-2.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
            >
              Add
            </button>
          </div>
          {form.tags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2" role="list" aria-label="Selected tags">
              {form.tags.map((tag) => (
                <span
                  key={tag}
                  role="listitem"
                  className="inline-flex items-center gap-1 rounded-full bg-brand-100 px-3 py-1 text-xs font-medium text-brand-800 dark:bg-brand-900/30 dark:text-brand-400"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => removeTag(tag)}
                    className="ml-0.5 rounded-full p-0.5 hover:bg-brand-200 dark:hover:bg-brand-800"
                    aria-label={`Remove tag ${tag}`}
                  >
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={submitting || !form.title.trim()}
          className="w-full rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500/50 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-brand-500 dark:hover:bg-brand-600"
        >
          {submitting ? "Creating..." : "Create Entry"}
        </button>
      </form>
    </div>
  );
}
