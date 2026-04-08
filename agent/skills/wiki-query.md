# Skill: Wiki Query

Answer a question by reading across the wiki, citing sources, and optionally filing the answer back as a new wiki page.

## When to Use

- When asking questions about your knowledge base
- When you want a synthesized answer grounded in your own collected material
- When you want to generate a briefing or report from your wiki

## Steps

### 1. Search the wiki

Read through `07-resources/` and `entities/` to find pages relevant to the question. Use:
- `bg find "{query}"` to search FalkorDB
- `bg think connect "{concept A}" "{concept B}"` if the question involves relationships
- `bg think audit "{claim}"` if the question is about verifying something
- File search across the vault for keyword matches

### 2. Synthesize an answer

Write a clear, structured answer that:
- **Cites specific wiki pages** using `[[wikilinks]]`
- **Quotes key claims** from source material
- **Notes disagreements** between sources if they exist
- **Identifies gaps** — "the wiki doesn't cover X yet"

### 3. Optionally file the answer

If the answer is substantive enough to be useful later, save it:
- As a new wiki article in `07-resources/` (if it's a topic overview)
- As a report in `outputs/` (if it's a one-time analysis)
- As an update to an existing wiki page (if it fills a gap)

Update `index.md` and `log.md` accordingly.

## Output Format

```markdown
## Answer

{Synthesized answer with [[wikilinks]] and citations}

## Sources Used

- [[Page 1]] — {what was relevant}
- [[Page 2]] — {what was relevant}

## Gaps Identified

- {Topic not covered in the wiki}
- {Claim that needs verification}
```
