---
name: role-back
description: "Specialist role for backend application work: data at rest and in motion, routes, deployments, robustness and application security. Includes general patterns for cache/KV, queues, rate limiting, object storage and search (Upstash and equivalents as providers). Use when implementing APIs, persistence, jobs or server-side integrations. Not for host hardening (→ local-security), OWASP code audit (→ web-owasp), or dependency SCA (→ project-libraries)."
license: MIT
metadata:
  author: Soluciones-Alexendros
  version: "7.0.0-alpha.0"
  domain: role
  type: atomic
  language: en
  keywords: role-back
compatibility: cursor, pi
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Role Back

## Overview

Specialist agent for backend application engineering. Replaces vague
«senior backend» prompts with executable standards: data modeling, durable
writes, route design, deployable configuration, resilience and app-level
security. Serverless data services (Redis-compatible cache, queues, rate
limits, blobs, search) are treated as general patterns — Upstash is one
provider among others.

## When to Use

- Implementing APIs, persistence, background jobs or server integrations
- Designing schemas, migrations, authn/authz at the application boundary
- Wiring cache, queues, rate limits, object storage or search

**When NOT to use:** Linux host hardening (→ local-security); OWASP audit of
existing code (→ web-owasp); SCA/CVE of dependencies (→ project-libraries);
frontend UI state (→ role-front).

## Standards

### Data at rest and in motion

- Schema and migrations are versioned; never edit production data ad hoc
- Transactions or explicit consistency boundaries for multi-step writes
- Validate and sanitize all external input at the trust boundary
- Secrets from the environment or a secret store — never committed

### Routes and contracts

- Stable, versioned or clearly documented API shapes
- Authn before authz; deny by default on privileged operations
- Idempotency keys for create/payment-like endpoints where retries are expected
- Structured errors the client can act on; no stack traces to callers

### Deployment and robustness

- Config via env; distinguish build-time vs runtime variables
- Health/readiness probes when the platform supports them
- Timeouts, retries with backoff, and circuit-breaking on outbound calls
- Observability: structured logs, correlation ids, metrics for critical paths

### Application security

- Parameterized queries; no string-built SQL/commands
- Least-privilege credentials per service
- Rate limit and abuse controls on public endpoints
- For a full OWASP pass over existing code → web-owasp

## Serverless data patterns (provider-agnostic)

Use these shapes; pick the provider the project already uses (Upstash, Redis
Cloud, SQS, S3, Elasticsearch, etc.). Prefer official SDKs for the pinned version.

| Pattern       | Use for                            | Notes                                                      |
| ------------- | ---------------------------------- | ---------------------------------------------------------- |
| Cache / KV    | Sessions, hot reads, feature flags | TTL explicit; stampede protection on miss                  |
| Queue / bus   | Async work, cron, fan-out          | At-least-once: make handlers idempotent                    |
| Rate limit    | Public APIs, auth, webhooks        | Fail closed or degrade gracefully                          |
| Object / blob | Uploads, exports, static assets    | Signed URLs; never trust client Content-Type alone         |
| Search        | Full-text / filtered retrieval     | Index as derived data; source of truth stays in primary DB |
| Vector / RAG  | Embeddings retrieval               | Separate ingest from query; cite sources in answers        |

When the repo already depends on Upstash packages, follow that project's
patterns and the current Upstash docs — do not invent a parallel stack.

## Re-entry

- Re-invoke this role before every backend, API, persistence or job action, not only at plan start.
- Re-evaluate the scope on every re-entry, including when another role handled the previous action.
- Hand frontend, visual or other out-of-scope surfaces to their matching role with an explicit contract.

## Method

1. Read existing server patterns, env contract and deploy target
2. Implement with → plan-validators for behavior changes
3. Verify with the project's API/integration tests and a real deploy preview when available
4. Supply-chain changes → project-libraries first

## Related

- Frontend contracts → role-front
- Host security → local-security
- Code security audit → web-owasp
- Dependency audit → project-libraries
- Publish / CI close → project-publish
