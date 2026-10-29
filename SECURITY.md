# Security policy

### Propósito de este documento

- **Objetivos:** Canal privado de vulnerabilidades, ventanas de respuesta y alcance (skills, validators y contrato de flota).
- **Estructura:** Esta meta-sección → Reportar → Ventanas → Alcance.
- **Contenido a integrar según contexto:** En un producto, cambia la URL de advisories y rellena versiones de aplicación. No desactives Dependabot Alerts ni secret scanning.

Report a vulnerability in a skill, a bundled script, the validators, or the fleet canon of this repository through GitHub private vulnerability reporting:

https://github.com/Soluciones-Alexendros/autoworkspace/security/advisories/new

Alternatively write to **operaciones@alexendros.dev** with description, impact, reproduction, and version (`package.json` or skill `metadata.version`).

Do not open a public issue for an exploitable finding in a script that runs on a host.

## Response windows

| Step                            | Target                                                     |
| ------------------------------- | ---------------------------------------------------------- |
| Acknowledgement                 | ≤ 48 business hours (Europe/Madrid)                        |
| Initial assessment              | ≤ 5 business days                                          |
| Patch / disclosure coordination | By severity; no exploitable detail until mitigation exists |

We acknowledge reports and, when a fix ships, credit the reporter in the changelog if they want that.

## Scope

- Skills, `tools/`, install scripts, and CI/validators of autoworkspace.
- Fleet contracts: docs, reusable workflows, `templates/product/`, Renovate and `main` protection conventions.
- Not covered: production secrets, customer credentials, or third-party product runtimes (report in those repos).
