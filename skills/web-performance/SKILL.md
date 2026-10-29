---
name: web-performance
description: "Web performance audit: Core Web Vitals (LCP, INP, CLS), Lighthouse 12, TTFB/FCP, rendering (SSR/SSG/ISR/islands), caching HTTP/CDN, load optimization and technical frontend diagnosis. Use when performing performance audit, Lighthouse/CWV, load optimization, stability visual, caching or technical frontend diagnosis. Not for compliance audits (→ web-compliance) nor backend load testing."
license: MIT
metadata:
  author: Soluciones-Alexendros (adapted)
  version: "7.0.0-alpha.0"
  domain: web
  type: atomic
  language: en
  keywords: web-performance
compatibility: cursor, pi
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Web Performance

## Overview

Web performance audit: Core Web Vitals (LCP, INP, CLS), Lighthouse 12, TTFB/FCP, rendering
(SSR/SSG/ISR/islands), caching HTTP/CDN, load optimization and technical frontend diagnosis.
Use when performing performance audit, Lighthouse/CWV, load optimization, stability
visual, caching or technical frontend diagnosis.

## When to Use

- When performance audit is requested
- For Lighthouse/CWV
- For load optimization
- For visual stability (CLS)
- For HTTP/CDN caching
- For technical frontend diagnosis

## Not for:

- Legal compliance or accessibility (→ web-compliance)

## Core Web Vitals

| Metric | Meaning                   | Good Threshold |
| ------ | ------------------------- | -------------- |
| LCP    | Largest Contentful Paint  | < 2.5s         |
| INP    | Interaction to Next Paint | < 200ms        |
| CLS    | Cumulative Layout Shift   | < 0.1          |

## Lighthouse 12

- Generates complete report
- Multiple categories
- Weighted scores

## Caching

- HTTP caching headers
- CDN configuration
- Strategic browser cache
