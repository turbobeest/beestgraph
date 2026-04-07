---
# ═══════════════════════════════════════════════════════════════
# TIER 1 — UNIVERSAL FIELDS (every document)
# ═══════════════════════════════════════════════════════════════
uid: ""                            # YYYYMMDDHHMM, auto-generated
title: ""
type: note                         # see Type Registry (docs/beestgraph-template-spec.md §8)
tags: []                           # 2-5 lowercase hyphenated tags
status: inbox                      # inbox | draft | published | archived
dates:
  created: null                    # when the file was created
  captured: null                   # when you encountered the info
  processed: null                  # when the agent last processed
  modified: null                   # last human edit

# ════��══════════════════════════════════════════════════════════
# TIER 2 — TYPE-CONDITIONAL FIELDS
# ═══════════════════════════════════════════════════════════════

# Identity extensions
aliases: []                        # alternative names (person, concept, tool)

# Provenance
source:
  type: manual                     # keepmd | obsidian_clipper | manual | api | agent
  url: ""                          # original URL (article, repo, thread, etc.)
  author: ""                       # creator of the source
  publisher: ""                    # site, publication, organization
  via: ""                          # how you found it
  context: ""                      # why you saved it

# Classification
para: resources                    # projects | areas | resources | archives
topics: []                         # hierarchical: ["technology/ai-ml"]
importance: 3                      # 1-5
confidence: 0.8                    # 0.0-1.0
content_stage: literature          # fleeting | literature | evergreen | reference

# Entities
entities:
  people: []
  concepts: []
  organizations: []
  tools: []
  places: []

# Engagement
engagement:
  status: unread                   # unread | read | reference
  rating: null                     # 1-5, optional
  last_visited: null

# Synthesis (AI-extracted)
summary: ""                        # 2-3 sentences
key_claims: []
questions: []
action_items: []

# Connections (mirror in body "## Connections" section!)
connections:
  supports: []
  contradicts: []
  extends: []
  supersedes: []
  inspired_by: []
  related: []

# Type-specific extensions
area: ""                           # for type: project
role: ""                           # for type: person
attendees: []                      # for type: meeting
project: ""                        # for type: meeting
scope: ""                          # for type: moc

# ═══════════════════════════════════════════════════════════════
# TIER 3 — ADVANCED FIELDS (add when earned)
# ═══════════════════════════════════════════════════════════════

# Structural hierarchy
up: []                             # ["[[Parent MOC]]"]

# Advanced temporal
# dates.published: null            # source publication date
# dates.event_date: null           # for events
# dates.due: null                  # for projects
# dates.reviewed: null             # last human re-evaluation
# dates.last_synthesis: null       # last AI graph-coherence check
# dates.expires: null              # knowledge expiration
# dates.archived: null             # archival timestamp

# Provenance integrity
# source.content_hash: ""          # SHA-256 at ingest
# source.archived_locally: false   # local copy in raw/?

# Epistemic
epistemic_effort: null             # casual | moderate | thorough

# Geospatial
location:
  name: ""
  lat: null
  lon: null
  region: ""

# Media
media:
  images: []
  attachments: []
  audio: []
  video: []

# Graph rendering hints
graph:
  cluster: null                    # auto-computed
  pinned: false
  hidden: false
  color_override: null

# Versioning
version: 1
---

(freeform markdown body)

## Connections

(none identified)
