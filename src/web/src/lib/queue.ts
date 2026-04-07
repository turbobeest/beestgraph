/**
 * Shared types and utilities for the queue review feature.
 */

export interface QueueItem {
  slug: string;
  title: string;
  type: string;
  topic: string;
  tags: string[];
  confidence: number | null;
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
  content_stage: "fleeting" | "evergreen";
}

export interface UpdateBody {
  type?: string;
  topic?: string;
  tags?: string[];
  confidence?: number | null;
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

/** Content type options from the type registry (spec S8). */
export const CONTENT_TYPES = [
  "article",
  "reference",
  "opinion",
  "tool",
  "film",
  "podcast",
  "book",
  "thread",
  "note",
  "bookmark",
  "repo",
] as const;

/** Map legacy type names to current spec values. */
export const LEGACY_TYPE_MAP: Record<string, string> = {
  "github-repo": "repo",
  tweet: "thread",
  paper: "article",
  tutorial: "reference",
  url: "article",
  video: "film",
  thought: "note",
  "social-post": "thread",
};

/** Map legacy quality strings to confidence numbers. */
export const LEGACY_QUALITY_MAP: Record<string, number> = {
  low: 0.3,
  medium: 0.5,
  high: 0.8,
};

/** Map legacy maturity values to content_stage values. */
export const LEGACY_MATURITY_MAP: Record<string, string> = {
  raw: "fleeting",
  permanent: "evergreen",
};

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

/** Confidence presets for the UI. */
export const CONFIDENCE_OPTIONS = [
  { label: "Low", value: 0.3 },
  { label: "Medium", value: 0.5 },
  { label: "High", value: 0.8 },
] as const;
