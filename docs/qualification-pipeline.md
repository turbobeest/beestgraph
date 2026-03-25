# Qualification Pipeline — Design Document

> The path from raw capture to permanent, enriched knowledge.

## Overview

Every piece of content entering beestgraph goes through a qualification pipeline before it earns permanent residency in the vault and graph. This ensures every item is properly categorized, tagged, and enriched — either through human review or intelligent auto-classification.

## Pipeline Stages

```
┌──────────────┐
│   CAPTURE    │  keep.md, Obsidian clipper, Telegram /add, Web UI, manual
└──────┬───────┘
       ▼
┌──────────────┐
│    INBOX     │  ~/vault/inbox/ — raw, unprocessed
│  status:     │  frontmatter status: inbox
│  inbox       │  watcher detects new .md file
└──────┬───────┘
       ▼
┌──────────────┐
│ QUALIFICATION│  ~/vault/queue/ — awaiting review
│  QUEUE       │  frontmatter status: qualifying
│              │  Telegram notification sent to user
│              │  User can: classify, tag, approve, reject
│              │  Timeout: auto-classify after N hours
└──────┬───────┘
       ▼
┌──────────────┐
│  ENRICHMENT  │  AI or manual metadata completion
│              │  - Content type assigned
│              │  - Topic categorized
│              │  - Entities extracted
│              │  - Summary generated
│              │  - Comprehensive frontmatter populated
└──────┬───────┘
       ▼
┌──────────────┐
│  PERMANENT   │  ~/vault/knowledge/<type>/<topic>/
│  RESIDENCY   │  frontmatter status: published
│              │  FalkorDB graph updated
│              │  Calendar event logged
└──────────────┘
```

## Content Types

Every document gets a `content_type` in its frontmatter. This determines where it lives in the vault and how it's displayed.

### Core types

| Type | Description | Example |
|------|-------------|---------|
| `article` | Blog post, news article, essay | Tech blog post about Rust |
| `paper` | Academic paper, research report | arXiv paper on LLMs |
| `tutorial` | How-to guide, walkthrough | "Setting up Docker on Pi" |
| `reference` | Documentation, API reference | Python stdlib docs |
| `thought` | Personal reflection, idea, opinion | "Why I think X about Y" |
| `note` | Quick note, snippet, observation | Meeting notes |

### Media types

| Type | Description | Example |
|------|-------------|---------|
| `video` | YouTube, Vimeo, etc. | Conference talk |
| `podcast` | Audio content | Tech podcast episode |
| `image` | Infographic, diagram, photo | Architecture diagram |
| `pdf` | PDF document | Whitepaper, manual |

### Social/web types

| Type | Description | Example |
|------|-------------|---------|
| `tweet` | X/Twitter post or thread | @karpathy thread on training |
| `social-post` | Other social media | LinkedIn post, Mastodon |
| `discussion` | Forum thread, HN, Reddit | HN discussion on knowledge graphs |
| `url` | Generic web page | Product page, landing page |

### Code types

| Type | Description | Example |
|------|-------------|---------|
| `github-repo` | GitHub repository | falkordb/falkordb |
| `github-issue` | Issue or PR | Bug report, feature request |
| `code-snippet` | Code block, gist | Useful Python snippet |
| `tool` | Software tool, CLI, app | A new CLI tool to try |

### Life types

| Type | Description | Example |
|------|-------------|---------|
| `recipe` | Food recipe | Sourdough bread recipe |
| `product` | Product page, review | Hardware review |
| `place` | Location, restaurant, venue | Coffee shop recommendation |
| `event` | Conference, meetup, deadline | PyCon 2026 |
| `person` | Profile, bio | Notable person to track |
| `book` | Book notes, review | "Thinking, Fast and Slow" |
| `course` | Online course, lecture series | MIT OCW lecture |

## Comprehensive Frontmatter Schema

```yaml
---
# === Identity ===
title: "Document Title"
content_type: article          # from content types above
slug: document-title           # URL-safe identifier

# === Source ===
source_url: "https://..."
source_type: keepmd | obsidian_clipper | telegram | manual | web_ui
source_domain: "example.com"
author: "Author Name"
date_published: 2026-03-24
date_captured: 2026-03-24T12:00:00Z
date_qualified: 2026-03-24T12:30:00Z   # when user approved
date_processed: 2026-03-24T12:31:00Z   # when AI enriched

# === Classification ===
status: inbox | qualifying | published | archived | rejected
para_category: projects | areas | resources | archives
topics:
  - technology/ai-ml
  - technology/programming
tags:
  - knowledge-graphs
  - python
  - falkordb
quality: high | medium | low   # user or AI assessment

# === AI Enrichment ===
summary: "Two to three sentence summary."
key_points:
  - "First key takeaway"
  - "Second key takeaway"
entities:
  people:
    - "Tim Berners-Lee"
  concepts:
    - "Knowledge Graph"
  organizations:
    - "Google"
  tools:
    - "FalkorDB"

# === Qualification ===
qualified_by: user | auto      # who approved it
qualification_notes: ""        # user's notes during review
related_to:                    # links to existing vault items
  - "knowledge-graphs-intro"

# === Type-specific fields ===
# (only present for certain content_types)
github_repo: "owner/repo"     # for github-repo type
github_stars: 1234
language: "Python"
tweet_author: "@handle"        # for tweet type
tweet_thread: false
recipe_servings: 4             # for recipe type
recipe_time: "45 minutes"
isbn: "978-..."                # for book type
doi: "10.1234/..."             # for paper type
---
```

## Telegram Qualification Flow

When a new item enters the inbox:

1. **Watcher detects file** → AI pre-classifies → moves to `~/vault/queue/`
2. **Bot sends Telegram message with AI recommendation:**
   ```
   📥 New item captured:

   Title: Introduction to Knowledge Graphs
   Source: https://example.com/kg-intro
   Captured via: keep.md

   🤖 My recommendation:
     Type: article
     Topic: technology/ai-ml
     Tags: knowledge-graphs, graph-databases, ai
     Quality: high
     Summary: An overview of knowledge graph architectures
     and their applications in AI systems.

   Reply:
     ✅ "ok" or "approve" — accept as-is
     ✏️ "type paper" — change the type
     ✏️ "topic science/cs" — change the topic
     ✏️ "add tag semantic-web" — add a tag
     ✏️ Any free text — I'll adjust based on your notes
     ⏰ "later" or "remind me at 9pm" — schedule a follow-up
     ❌ "reject" — archive it
   ```
3. **User responds** (or doesn't):
   - `ok` / `approve` / `👍` → accept AI recommendation → enrich → permanent
   - `type paper` → update content_type, re-present for approval
   - `topic business/startups` → update topic, re-present
   - `add tag X` / `remove tag Y` → modify tags
   - `quality low` → downgrade quality assessment
   - Free text reply → Claude interprets intent, adjusts classification, re-presents
   - `later` → stay in queue, remind in 4 hours
   - `remind me at 9pm` / `remind me tomorrow` → schedule specific follow-up (calendar event)
   - `reject` → move to ~/vault/archives/rejected/
   - No response → auto-classify using AI recommendation after `qualification_timeout` hours

4. **Conversational refinement:**
   The bot maintains context for each qualifying item. Multiple back-and-forth exchanges
   are supported:
   ```
   User: "this is more of a tutorial than an article"
   Bot: "Got it. Updated:
         Type: tutorial (was: article)
         Everything else unchanged. Approve?"
   User: "also add tag self-hosted"
   Bot: "Added. Final classification:
         Type: tutorial
         Topic: technology/ai-ml
         Tags: knowledge-graphs, graph-databases, ai, self-hosted
         Approve?"
   User: "ok"
   Bot: "✅ Published to knowledge/tutorials/technology/ai-ml/"
   ```

5. **Scheduled reminders:**
   When a user says "later" or "remind me at X", the bot:
   - Creates a calendar event in Radicale at the requested time
   - When that time arrives, re-sends the qualification message
   - Items can be deferred multiple times

## Configuration

```yaml
qualification:
  enabled: true
  timeout_hours: 24            # auto-classify after this
  notify_telegram: true        # send Telegram notification
  auto_classify_fallback: true # use AI if no response
  queue_dir: queue             # subdirectory in vault
```

## Vault Structure (updated)

```
~/vault/
├── inbox/          ← raw captures land here
├── queue/          ← qualifying items (awaiting review)
├── knowledge/      ← permanent: organized by type and topic
│   ├── articles/
│   │   ├── technology/
│   │   └── science/
│   ├── papers/
│   ├── tutorials/
│   ├── tweets/
│   ├── github-repos/
│   ├── recipes/
│   ├── books/
│   └── notes/
├── projects/       ← PARA: active projects
├── areas/          ← PARA: ongoing responsibilities
├── resources/      ← PARA: reference material
├── archives/       ← PARA: completed/inactive + rejected items
├── daily/          ← daily notes
└── templates/      ← frontmatter templates per content type
```
