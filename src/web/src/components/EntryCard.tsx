import { STATUS_LABELS } from "@/lib/constants";

interface EntryCardProps {
  title: string;
  summary: string;
  status: string;
  sourceType: string;
  sourceUrl: string;
  createdAt: string;
}

function StatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    inbox: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
    processing: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
    published: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    archived: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400",
  };

  const colors = colorMap[status] ?? colorMap["inbox"];

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colors}`}>
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}

function formatDate(iso: string): string {
  if (!iso) return "";
  try {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export default function EntryCard({
  title,
  summary,
  status,
  sourceType,
  sourceUrl,
  createdAt,
}: EntryCardProps) {
  return (
    <article className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md dark:border-gray-700 dark:bg-gray-800">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-base font-semibold leading-tight">
          {sourceUrl ? (
            <a
              href={sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-brand-600 dark:hover:text-brand-400"
            >
              {title || "Untitled"}
            </a>
          ) : (
            title || "Untitled"
          )}
        </h3>
        <StatusBadge status={status} />
      </div>
      {summary && (
        <p className="mt-2 line-clamp-2 text-sm text-gray-600 dark:text-gray-400">{summary}</p>
      )}
      <div className="mt-3 flex items-center gap-3 text-xs text-gray-500 dark:text-gray-500">
        {sourceType && (
          <span className="rounded bg-gray-100 px-1.5 py-0.5 dark:bg-gray-700">{sourceType}</span>
        )}
        {createdAt && <time dateTime={createdAt}>{formatDate(createdAt)}</time>}
      </div>
    </article>
  );
}
