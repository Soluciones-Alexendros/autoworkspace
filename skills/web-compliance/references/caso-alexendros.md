# Caso de referencia — alexendros.dev (baseline a re-verificar)

Hallazgos documentados en el material fuente para el dominio personal `alexendros.dev` (Astro 4.16 + Vercel, canonical apex según el ADR de producto de ese sitio). **Usar solo como hipótesis de partida: re-verificar todo con `scripts/audit_page.py` y revisión manual antes de incluirlo en un informe.**

## Baseline documentado

- ✅ HTTPS forzado en Vercel, HSTS, canonical apex autorreferenciado, landmarks semánticos (`header/nav/main/footer`), contraste OKLCH conforme, alt en imágenes de portfolio, jerarquía H1–H3 coherente, titles únicos con marca personal.
- ❌ **ACC-04 Crítico**: no hay skip link "saltar al contenido" → bloquea WCAG 2.4.1. Fix ~15 min (template en `remediation.md`).
- ❌ **TEC-08 Alto**: falta JSON-LD `Person` (autor con `sameAs` a GitHub/LinkedIn), `Organization` y `Service`. Fix <1 h, validar en Rich Results Test.
- ❌ **ANA-01/LEG-01 Crítico si hay analítica**: si usa Vercel Analytics o GA4 sin CMP, falta Consent Mode v2 + política de cookies/privacidad enlazadas en footer. Fix ~1 h con CMP (CookieYes/Usercentrics).
- ⚠️ **TEC-05/TEC-09**: verificar `/sitemap-index.xml` (generado por @astrojs/sitemap) y `robots.txt` con `Sitemap:` declarado; `lastmod` veraz; validar en GSC.
- ⚠️ **ONP-04**: autor explícito, pero mejorable con página `/sobre-mi` (bio extensa, credenciales, foto, enlaces verificables) → sube E-E-A-T de PASS a excelente.
- ➖ SEM: sin campañas activas → pilar N/A justificado; considerar brand search futuro.

## Dictamen documentado

POSITIVO CON RESERVAS → al corregir los 3 FAIL (Sprint 1, ~2 h total en branch `feat/a11y-jsonld-consent`), el dominio alcanzaría dictamen POSITIVO pleno conforme a EN 301 549 / WCAG 2.2 AA.
