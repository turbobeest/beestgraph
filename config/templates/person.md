---
# Person template — derived from universal.md
# For: individuals referenced across the graph

# Tier 1
uid: ""
title: "{{ title }}"
type: person
tags: []
status: inbox
dates:
  created: {{ created }}
  captured: {{ captured }}
  processed: null
  modified: {{ created }}

# Tier 2 — person priority fields
aliases: []
role: ""
source:
  type: manual
para: resources
topics: []
importance: 3
entities:
  people:
    - "{{ title }}"
  organizations: []
  places: []
summary: ""
connections:
  related: []
version: 1
---

## About

{{ summary }}

## Affiliations

## Notable Work

## Connections

(none identified)
