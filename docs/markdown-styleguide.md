# beestgraph Markdown Style Guide

> Standards for content formatting, structure, and readability inside every markdown note.

**Status:** DESIGN — requires review before implementation.

---

## Purpose

This style guide defines how markdown content should be formatted *inside* the note body. It complements:
- **Frontmatter schema** — what metadata surrounds the content
- **Folder structure** — where the file lives
- **Graph schema** — how it connects to other notes

The style guide is applied progressively through the pipeline:

```
Capture (raw)
  │  → Auto-formatting applied (headings, links, whitespace, encoding)
  ▼
Inbox (cleaned)
  │  → AI enrichment (summary, key points, entities injected into frontmatter)
  ▼
Queue (qualifying)
  │  → Human review via Telegram (content type, topic, tags confirmed)
  ▼
Fleeting (graduated)
  │  → Meets readability criteria (structure validated, style enforced)
  ▼
Permanent (published)
      → Fully compliant with style guide
```

### What's automatic vs human

| Stage | What happens | Who |
|-------|-------------|-----|
| Inbox arrival | Encoding fix, whitespace cleanup, heading normalization, link format standardization | Automatic |
| Queue entry | Summary generated, key points extracted, entities identified, content type classified | AI (Claude) |
| Qualification | Type/topic/tags confirmed, quality assessed | Human (Telegram) |
| Fleeting graduation | Content structure validated against type template | Automatic + human |
| Permanent publication | Full style compliance verified | Automatic |

---

## 1. Document Structure

### Every note follows this skeleton

```markdown
---
(frontmatter — see vault-schema-design.md)
---

# Title

> One-line summary (mirrors frontmatter `summary` field)

## Content

(The actual body — varies by content type)

## Key Takeaways

- Point 1
- Point 2
- Point 3

## Connections

- Related: [[Other Note]]
- See also: [[Another Note]]
- Contradicts: [[Opposing View]]

## Sources

- [Original article](https://example.com)
- Captured via: keep.md / clipper / telegram
```

### Rules

1. **One H1 only** — the document title. Must match frontmatter `title`.
2. **H2 for sections** — never skip heading levels (no H1 → H3).
3. **Summary block** — a blockquote immediately after H1 summarizing the note in 1-2 sentences.
4. **Key Takeaways** — required for `article`, `paper`, `tutorial`, `video`, `book` types. 3-5 bullet points.
5. **Connections** — wiki-links to related notes. Not required for `fleeting` maturity.
6. **Sources** — link to original source. Always present for external captures.

---

## 2. Content Type Templates

### article / reference / url

```markdown
# {title}

> {summary}

## Content

{body — original content or annotated summary}

## Key Takeaways

- {point 1}
- {point 2}
- {point 3}

## Connections

- Related: [[{related note}]]

## Sources

- [{source_domain}]({source_url})
```

### paper

```markdown
# {title}

> {summary}

## Abstract

{abstract or AI-generated abstract}

## Key Findings

- {finding 1}
- {finding 2}

## Methodology

{brief methodology summary if applicable}

## Key Takeaways

- {point 1}
- {point 2}

## Connections

- Related: [[{related note}]]

## Sources

- [DOI: {doi}](https://doi.org/{doi})
- [arXiv: {arxiv_id}](https://arxiv.org/abs/{arxiv_id})
```

### tutorial

```markdown
# {title}

> {summary}

## Prerequisites

- {prerequisite 1}
- {prerequisite 2}

## Steps

### Step 1: {step title}

{step content}

### Step 2: {step title}

{step content}

## Key Takeaways

- {point 1}

## Connections

- Related: [[{related note}]]

## Sources

- [{source_domain}]({source_url})
```

### tweet

```markdown
# {title}

> {summary}

## Thread

> {tweet content — blockquoted}
>
> — @{handle}, {date}

{optional: annotation or commentary}

## Key Takeaways

- {point 1}

## Connections

- Related: [[{related note}]]

## Sources

- [@{handle}]({tweet_url})
```

### github-repo

```markdown
# {title}

> {summary}

## Overview

{repository description}

**Language:** {language}
**Stars:** {stars} | **License:** {license}

## Why This Matters

{personal annotation — why you saved this}

## Key Features

- {feature 1}
- {feature 2}

## Connections

- Related: [[{related note}]]

## Sources

- [GitHub: {owner}/{repo}]({source_url})
```

### video

```markdown
# {title}

> {summary}

## Notes

{timestamped notes or AI-generated transcript summary}

- **00:00** — {topic}
- **05:30** — {topic}
- **12:00** — {topic}

## Key Takeaways

- {point 1}
- {point 2}

## Connections

- Related: [[{related note}]]

## Sources

- [{channel}]({source_url}) ({duration})
```

### book

```markdown
# {title}

> {summary}

## Highlights

> {quote or highlight 1}

{annotation}

> {quote or highlight 2}

{annotation}

## Key Takeaways

- {point 1}
- {point 2}
- {point 3}

## Connections

- Related: [[{related note}]]

## Sources

- ISBN: {isbn}
- Author: {author}
```

### recipe

```markdown
# {title}

> {summary}

## Ingredients

- {quantity} {ingredient}
- {quantity} {ingredient}

## Instructions

1. {step 1}
2. {step 2}
3. {step 3}

## Notes

{personal notes, modifications, results}

## Sources

- [{source_domain}]({source_url})
```

### fleeting / note / thought

```markdown
# {title}

> {one-line context}

{free-form content — minimal structure required}

## Connections

- Sparked by: [[{source note}]]
- Related: [[{related note}]]
```

### person

```markdown
# {name}

> {one-line description — role, affiliation}

## About

{brief bio or context for why this person is in the graph}

## Notable Work

- {work 1}
- {work 2}

## Connections

- Mentioned in: [[{note 1}]]
- Related: [[{related person or concept}]]
```

### project (PARA)

```markdown
# {project name}

> {one-line project goal}

## Objective

{what does "done" look like?}

## Status

- [ ] {task 1}
- [x] {completed task}
- [ ] {task 2}

## Key Decisions

- {decision 1} — {rationale}

## Resources

- [[{related note}]]
- [{external link}]({url})
```

---

## 3. Formatting Rules

### Text

| Rule | Standard | Example |
|------|----------|---------|
| Line length | Soft wrap, no hard breaks within paragraphs | (let the editor handle it) |
| Paragraphs | Separated by one blank line | |
| Emphasis | `**bold**` for key terms, `*italic*` for titles/names | **knowledge graph**, *Thinking, Fast and Slow* |
| Inline code | `` `backticks` `` for code, commands, file paths | `pip install falkordb` |
| Abbreviations | Spell out on first use, abbreviate after | "Personal Knowledge Management (PKM)" then "PKM" |

### Headings

| Rule | Standard |
|------|----------|
| H1 | Document title only, once per file |
| H2 | Major sections |
| H3 | Subsections |
| H4+ | Avoid — flatten the hierarchy |
| Capitalization | Title Case for H1, Sentence case for H2-H3 |
| No trailing punctuation | `## Key takeaways` not `## Key takeaways:` |

### Links

| Type | Format |
|------|--------|
| Internal (wiki-link) | `[[Note Title]]` |
| Internal with display | `[[Note Title\|display text]]` |
| External | `[display text](https://url)` |
| No bare URLs | Always wrap in `[text](url)` format |

### Lists

| Rule | Standard |
|------|----------|
| Unordered | Use `-` (not `*` or `+`) |
| Ordered | Use `1.` for all items (auto-numbering) |
| Nesting | Max 2 levels deep |
| Terminal punctuation | No periods on single-phrase items; periods on full sentences |

### Code

| Rule | Standard |
|------|----------|
| Inline | `` `code` `` for short references |
| Blocks | Triple backtick with language identifier |
| Language tag | Always specify: ` ```python `, ` ```bash `, ` ```cypher ` |

### Blockquotes

| Use | Format |
|-----|--------|
| Quotes from sources | `> quoted text` with attribution |
| Summary/callout | `> one-line summary` after H1 |
| Tweet content | Blockquoted with author attribution |

### Images and attachments

| Rule | Standard |
|------|----------|
| Embed | `![[filename]]` for vault attachments |
| Alt text | `![[filename\|alt text description]]` |
| Naming | `{zettelkasten_id}-{slug}-{description}.{ext}` |
| Location | Always in `09-attachments/` |

### Whitespace

| Rule | Standard |
|------|----------|
| Trailing whitespace | None — strip on save |
| Trailing newline | One blank line at end of file |
| Consecutive blank lines | Max 1 (no double-blanks) |
| Heading spacing | One blank line before and after each heading |
| List spacing | No blank lines between list items |

---

## 4. Readability Criteria

### Graduation requirements: inbox → fleeting

| Criterion | Required | How |
|-----------|----------|-----|
| Valid frontmatter | Yes | Automatic validation |
| Title present | Yes | Frontmatter `title` field |
| Content not empty | Yes | Body has > 0 words |
| Encoding is UTF-8 | Yes | Auto-converted on capture |
| No bare URLs in body | No | Warned, not blocked |

### Graduation requirements: fleeting → permanent

| Criterion | Required | How |
|-----------|----------|-----|
| All fleeting criteria | Yes | — |
| Summary present | Yes | Frontmatter or blockquote after H1 |
| Content type assigned | Yes | Frontmatter `type` |
| At least 1 topic | Yes | Frontmatter `topics` |
| At least 1 tag | Yes | Frontmatter `tags` |
| H1 matches title | Yes | Auto-enforced |
| Key Takeaways section | For applicable types | See §2 |
| Sources section | For external captures | Link to original |
| No heading level skips | Yes | Linted |
| Wiki-links use [[]] | Yes | Auto-converted |
| Code blocks have language | Warned | Linted |

---

## 5. Auto-Formatting Pipeline

These transformations are applied automatically at each stage:

### On capture (inbox arrival)

```python
def auto_format_on_capture(content: str) -> str:
    """Applied to every file entering the inbox."""
    # 1. Fix encoding to UTF-8
    # 2. Normalize line endings to LF
    # 3. Strip trailing whitespace from each line
    # 4. Ensure single trailing newline
    # 5. Collapse 3+ consecutive blank lines to 2
    # 6. Normalize heading whitespace (blank line before/after)
    # 7. Convert bare URLs to [url](url) format
    # 8. Normalize list markers (*/+ → -)
    # 9. Ensure H1 exists (add from title if missing)
```

### On qualification (queue entry)

```python
def auto_format_on_qualify(content: str, frontmatter: dict) -> str:
    """Applied when moving to the qualification queue."""
    # 1. All capture formatting
    # 2. Inject summary blockquote after H1 (from AI summary)
    # 3. Add Key Takeaways section if applicable type and missing
    # 4. Add Sources section if source_url present and missing
    # 5. Add Connections section placeholder if missing
    # 6. Normalize wiki-link format
```

### On publication (permanent graduation)

```python
def validate_for_publication(content: str, frontmatter: dict) -> list[str]:
    """Validate style compliance. Returns list of issues (empty = pass)."""
    # 1. H1 matches frontmatter title
    # 2. No heading level skips
    # 3. Key Takeaways present (for applicable types)
    # 4. Sources present (for external captures)
    # 5. No bare URLs
    # 6. Code blocks have language tags
    # 7. Summary blockquote present
```

---

## 6. Source-Specific Normalization

Different capture sources produce different raw formats. The pipeline normalizes them:

| Source | Raw format | Normalization |
|--------|-----------|---------------|
| **keep.md** | Clean markdown with metadata | Minimal — already well-formatted |
| **Obsidian Web Clipper** | Full HTML-to-markdown with frontmatter | Strip clutter, normalize headings |
| **Telegram /add** | URL only, no content | Fetch page, extract article text |
| **Web UI /entry** | URL + title + notes | Fetch page, merge with user notes |
| **Manual (Obsidian)** | User-written markdown | Validate structure only |
| **Notion export** | Markdown with Notion-specific syntax | Convert Notion callouts, databases |
| **Anytype export** | Protobuf/markdown hybrid | Extract markdown content |
| **PDF** | Binary → text extraction | OCR/text extract, structure recovery |
| **YouTube** | Transcript + metadata | Format as timestamped notes |

### Extensibility

The normalization pipeline is plugin-based. Each source has a normalizer:

```python
class SourceNormalizer(Protocol):
    def can_handle(self, source_type: str, content: str) -> bool: ...
    def normalize(self, content: str, metadata: dict) -> tuple[str, dict]: ...
```

New sources (Notion, Anytype, Readwise, etc.) are added by implementing this interface.

---

## 7. Graph Schema Implications

The three organizational methods map directly to the knowledge graph:

### PARA → Actionability edges

```cypher
(Document)-[:IN_PROJECT]->(Project)
(Document)-[:IN_AREA]->(Area)
// Resources = default (no explicit edge needed)
// Archive = status field
```

### Zettelkasten → Maturity and lineage

```cypher
(Document {maturity: 'fleeting|permanent'})
(Document)-[:GRADUATED_FROM]->(Document)  // fleeting → permanent
(Document)-[:SPARKED_BY]->(Document)      // idea origin
(Document)-[:SUPERSEDES]->(Document)      // updated thinking
```

### Topic Tree → Navigation hierarchy

```cypher
(Document)-[:BELONGS_TO]->(Topic)
(Topic)-[:SUBTOPIC_OF]->(Topic)
(Document)-[:IN_MOC]->(MOC)
(MOC)-[:CHILD_OF]->(MOC)
```

### Content type → Structure expectations

```cypher
(Document {content_type: 'article|paper|tweet|...'})
// The content_type determines which template and validation rules apply
```

All three schemas coexist on the same nodes. A single document can be:
- `IN_PROJECT` (PARA: actionable)
- `maturity: permanent` (Zettelkasten: fully processed)
- `BELONGS_TO technology/ai-ml` (Topic: navigable)
- `IN_MOC Knowledge Graphs MOC` (curated collection)

---

## 8. Adoption by Other Projects

This style guide is designed to be adoptable independently of beestgraph:

- **The rules** (§3-4) work for any Obsidian vault
- **The templates** (§2) work with any markdown-based PKM
- **The auto-formatting** (§5) can be extracted as a standalone tool
- **The graph schema** (§7) requires FalkorDB but the concepts map to any graph DB

Other projects can fork this style guide and customize:
- Add/remove content types
- Adjust readability criteria
- Change graduation requirements
- Swap the graph backend

The `obsidian-headless-cli` (separate repo) could eventually include a `vault lint` command that validates against a configurable style guide.
