# Skill: Wiki Lint

Health-check the wiki for contradictions, orphans, missing cross-references, stale claims, and structural gaps. This is Karpathy's "lint" operation — run it monthly or whenever the wiki feels stale.

## When to Use

- Monthly maintenance
- After a large batch of ingests
- When `bg health` reports orphan documents
- When the Obsidian graph view shows disconnected clusters

## Steps

### 1. Find orphan pages

Scan all `.md` files in `07-resources/` and `entities/`. An orphan is a page that:
- Has zero incoming `[[wikilinks]]` from other pages
- Has zero outgoing `[[wikilinks]]` to other pages

Report: list of orphans with recommendation (add links, merge, or archive).

### 2. Find broken wikilinks

Scan all `.md` files for `[[Link Target]]` references where no matching `.md` file exists anywhere in the vault. These are "ghost nodes" in the Obsidian graph.

Report: list of broken links with the file they appear in.
Action: either create the missing page or fix the link.

### 3. Find contradictions

For each file with `key_claims` in frontmatter, search all other files for conflicting claims on the same topic.

Run: `bg think audit "{claim}"` for each claim.

Report: pairs of documents with conflicting claims, with the specific text.

### 4. Find stale content

Flag documents where:
- `dates.modified` is older than 90 days AND the topic has newer documents
- `source.url` returns HTTP 404 (dead source)
- `status` is still `inbox` or `qualifying` (stuck in pipeline)

### 5. Find missing entity pages

Scan all `[[wikilinks]]` that point to names in `entities/` directories. Check if the entity page exists. If not, create it using the wiki-compile entity template.

### 6. Suggest new articles

Based on:
- Frequently mentioned concepts that don't have their own article
- Topics where only 1 article exists (thin coverage)
- Entity pages with 5+ mentions but no dedicated deep-dive article

Report: "Suggested new wiki articles" with rationale.

### 7. Write report

Save the lint report to `00-meta/wiki-lint-{date}.md` with sections for each check above. Append summary to `log.md`.

## Output Format

```markdown
# Wiki Lint Report — {date}

## Summary
- Pages scanned: {n}
- Orphans found: {n}
- Broken links: {n}
- Contradictions: {n}
- Stale pages: {n}
- Missing entities: {n}
- Suggested articles: {n}

## Orphan Pages
...

## Broken Links
...

## Contradictions
...

## Stale Content
...

## Missing Entity Pages
...

## Suggested New Articles
...
```
