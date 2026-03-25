/**
 * Shared types and utilities for the queue review feature.
 */

export interface QueueItem {
  slug: string;
  title: string;
  type: string;
  topic: string;
  tags: string[];
  visibility: string;
  quality: string;
  summary: string;
  securityFindings: string;
  filename: string;
  dateCaptured: string;
  sourceUrl: string;
}

export interface QueueItemDetail extends QueueItem {
  content: string;
  frontmatter: Record<string, unknown>;
}

export interface ApproveBody {
  maturity: "fleeting" | "permanent";
  visibility?: "public" | "private" | "shared";
}

export interface UpdateBody {
  type?: string;
  topic?: string;
  tags?: string[];
  visibility?: string;
  quality?: string;
  summary?: string;
}

/** Generate a URL-safe slug from a filename. */
export function slugFromFilename(filename: string): string {
  return filename
    .replace(/\.md$/i, "")
    .replace(/\s+/g, "-")
    .toLowerCase();
}

/** Reverse a slug back to a potential filename pattern. */
export function filenameFromSlug(slug: string): string {
  return `${slug}.md`;
}

/** Content type options from the taxonomy. */
export const CONTENT_TYPES = [
  "article",
  "tutorial",
  "reference",
  "opinion",
  "tool",
  "video",
  "podcast",
  "book",
  "paper",
  "thread",
  "note",
  "bookmark",
] as const;

/** Topic options from the taxonomy. */
export const TOPICS = [
  "technology",
  "technology/programming",
  "technology/ai-ml",
  "technology/infrastructure",
  "technology/security",
  "technology/web",
  "science",
  "science/physics",
  "science/biology",
  "science/mathematics",
  "business",
  "business/startups",
  "business/finance",
  "business/marketing",
  "culture",
  "culture/books",
  "culture/film",
  "culture/music",
  "culture/history",
  "health",
  "health/fitness",
  "health/nutrition",
  "health/mental-health",
  "personal",
  "personal/journal",
  "personal/goals",
  "personal/relationships",
  "meta",
  "meta/pkm",
  "meta/tools",
  "meta/workflows",
] as const;

export const VISIBILITY_OPTIONS = ["private", "shared", "public"] as const;
