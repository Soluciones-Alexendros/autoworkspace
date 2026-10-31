# P8 · Repos especiales · clienteafirma-alexendros, sysXray, archmaker (un PR por repo)

```
clienteafirma-alexendros (fork de ctt-gob-es/clienteafirma, rama master, Java):
- ci-gate con needs de quality, test, build, smoke, build-linux-jdk8, crypto-validation, f2-vectors y accessibility (código).
- Arregla Dependency Review (rojo en master), Generate SBOM y Merge SARIF.
- Orca GUI experimental queda fuera del ci-gate (continue-on-error documentado).
- NO introduzcas release-please: conserva release.yml y los tags estilo upstream.
- automerge.yml. Los PRs de sync con upstream se fusionan con merge commit: el auto-merge para PRs cuya rama empiece por `upstream-sync/` usa --merge en vez de --squash.
sysXray (Soluciones-Alexendros, GitHub Pages, sin CI ni protección):
- ci.yml con el reusable static (build + enlaces) + ci-gate; pages.yml solo despliega tras push a main.
- release-please simple, package-kind none; renovate.json de flota; automerge.yml.
archmaker (Alexendros, Tauri + Rust + TS):
- Coordina con /workspace/10-ingenieros/github-audit/2026-10-25/plan-archmaker-reorientacion.md: si F1–F2 están en curso, este PR solo añade ci-gate (needs de los jobs actuales G0–G10) y automerge.
- Sustituye plan-release.yml/release.yml por release-please (versión = tag v0.2.0) y tauri-apps/tauri-action (AppImage + deb) + SHA256SUMS + attestation. La ISO, si iso.yml la produce, se adjunta igual.
- Ruleset actual "Protect main (externals)" con bypass always para el rol admin: se sustituye en P9, no aquí.
- Si la App no está instalada en la cuenta personal, deja automerge/release preparados pero desactivados y anótalo.
Criterios de éxito: ci-gate verde en los 4 repos; 0 dependabot.yml en la flota (gh search code "filename:dependabot.yml org:Soluciones-Alexendros" → vacío); releases automáticos donde aplica.
Último paso obligatorio: actualiza el apartado «P8 · Repos especiales» en la página de Notion de la política (NOTION_POLICY_PAGE), con una fila por repo.
```
