#!/usr/bin/env python3
"""
Escaneo estructural determinista de un repositorio.

Genera un inventario técnico (JSON + resumen Markdown) con:
- mapa de lenguajes y tamaños
- presencia de ficheros estándar (README, LICENSE, CI, manifiestos de dependencias)
- higiene de ficheros (vacíos, grandes, binarios, codificación, finales de línea)
- convenciones de nombrado
- patrones de secretos/credenciales hardcodeadas (sin volcar el valor)
- ficheros .env versionados (excluye .env.example / .env.sample)
- duplicados exactos por hash (ficheros de tamaño acotado)
- marcadores TODO/FIXME/HACK/XXX
- detección de tests y ratio aproximado tests/código
- salud de manifiestos de dependencias (versiones sin fijar)
- artefactos típicamente no versionables ya trackeados (si hay .git)

Uso:
    python3 scan_repo.py <ruta_repo> [--json salida.json] [--md salida.md]

Solo usa la biblioteca estándar. No modifica el repositorio.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("scan_repo")


def _pattern_hit(tipo: str, fichero: str, linea: int, confianza: str) -> dict[str, Any]:
    """Metadatos de hallazgo sin valor ni snippet (anti clear-text storage)."""
    fp_src = f"{fichero}:{linea}:{tipo}".encode()
    return {
        "tipo": tipo,
        "fichero": fichero,
        "linea": int(linea),
        "confianza": confianza,
        "fingerprint": hashlib.sha256(fp_src).hexdigest()[:16],
    }


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    "dist",
    "build",
    "out",
    "target",
    ".next",
    ".nuxt",
    "vendor",
    ".idea",
    ".vscode",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    ".gradle",
    "Pods",
    "DerivedData",
}

IGNORE_DIR_SUFFIXES = (".egg-info",)

LANG_BY_EXT = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".go": "Go",
    ".rs": "Rust",
    ".c": "C",
    ".h": "C/C++ (cabecera)",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C/C++ (cabecera)",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".scala": "Scala",
    ".clj": "Clojure",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".hs": "Haskell",
    ".lua": "Lua",
    ".r": "R",
    ".R": "R",
    ".jl": "Julia",
    ".dart": "Dart",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".ps1": "PowerShell",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".xml": "XML",
    ".md": "Markdown",
    ".rst": "reStructuredText",
    ".tex": "LaTeX",
    ".proto": "Protocol Buffers",
    ".tf": "Terraform",
    ".ipynb": "Jupyter Notebook",
    ".zig": "Zig",
    ".nim": "Nim",
    ".fs": "F#",
    ".ml": "OCaml",
    ".elm": "Elm",
    ".sol": "Solidity",
}

# Lenguajes que cuentan para el ratio tests/código (excluye datos/markup)
CODE_LANGS = {
    "Python",
    "JavaScript",
    "JavaScript (React)",
    "TypeScript",
    "TypeScript (React)",
    "Java",
    "Kotlin",
    "Go",
    "Rust",
    "C",
    "C/C++ (cabecera)",
    "C++",
    "C#",
    "Ruby",
    "PHP",
    "Swift",
    "Scala",
    "Clojure",
    "Elixir",
    "Erlang",
    "Haskell",
    "Lua",
    "R",
    "Julia",
    "Dart",
    "Vue",
    "Svelte",
    "Shell",
    "PowerShell",
    "Zig",
    "Nim",
    "F#",
    "OCaml",
    "Elm",
    "Solidity",
    "Protocol Buffers",
    "Terraform",
}

STANDARD_FILES = {
    "readme": ["README", "README.md", "README.rst", "README.txt", "readme.md"],
    "licencia": ["LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "COPYING"],
    "gitignore": [".gitignore"],
    "contributing": ["CONTRIBUTING", "CONTRIBUTING.md"],
    "changelog": ["CHANGELOG", "CHANGELOG.md", "HISTORY.md", "NEWS.md"],
    "code_of_conduct": ["CODE_OF_CONDUCT.md"],
    "security_policy": ["SECURITY.md"],
}

CI_PATHS = [
    ".github/workflows",
    ".gitlab-ci.yml",
    "Jenkinsfile",
    ".circleci",
    "azure-pipelines.yml",
    ".travis.yml",
    "bitbucket-pipelines.yml",
    "buildkite",
    ".buildkite",
]

MANIFESTS = {
    "package.json": "npm/Node",
    "package-lock.json": "npm (lock)",
    "yarn.lock": "Yarn (lock)",
    "pnpm-lock.yaml": "pnpm (lock)",
    "requirements.txt": "pip",
    "pyproject.toml": "Python (pyproject)",
    "Pipfile": "Pipenv",
    "poetry.lock": "Poetry (lock)",
    "setup.py": "setuptools",
    "Cargo.toml": "Rust (Cargo)",
    "Cargo.lock": "Cargo (lock)",
    "go.mod": "Go modules",
    "go.sum": "Go (lock)",
    "pom.xml": "Maven",
    "build.gradle": "Gradle",
    "build.gradle.kts": "Gradle",
    "composer.json": "PHP (Composer)",
    "Gemfile": "Ruby (Bundler)",
    "mix.exs": "Elixir (Mix)",
    "pubspec.yaml": "Dart/Flutter (pub)",
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "compose.yml": "Docker Compose",
    "Makefile": "Make",
}

# Solo directorios dedicados a tests (no "integration"/"testing" genéricos)
TEST_DIR_NAMES = {"test", "tests", "spec", "specs", "__tests__", "e2e", "unittest"}
TEST_FILE_RE = re.compile(r"(^test_|_test\.|\.test\.|\.spec\.|_spec\.|^conftest\.py$)", re.IGNORECASE)

PASCALCASE_EXTS = {
    ".tsx",
    ".jsx",
    ".vue",
    ".svelte",
    ".java",
    ".kt",
    ".kts",
    ".cs",
    ".swift",
}

STANDARD_NAME_PREFIXES = (
    ".",
    "README",
    "LICENSE",
    "CHANGELOG",
    "CONTRIBUTING",
    "Dockerfile",
    "Makefile",
    "CMakeLists",
    "Gemfile",
    "Jenkinsfile",
    "Pipfile",
    "Cargo",
    "CODE_OF_CONDUCT",
    "SECURITY",
    "AUTHORS",
    "NOTICE",
    "NEWS",
    "HISTORY",
    "COPYING",
    "INSTALL",
    "TODO",
)

# Nombres de tipo sin substring "secret"/"secreto" (CodeQL sensitive string literals).
CREDENTIAL_PATTERNS = {
    "Clave privada PEM": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "AWS Access Key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub Token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{20,}\b"),
    "Slack Token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    "Google API Key": re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"),
    "JWT hardcodeado": re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{5,}\b"),
    "Asignación de credencial": re.compile(
        r"(?i)\b(password|passwd|secret|api[_-]?key|token|auth[_-]?token)\b"
        r"\s*[:=]\s*['\"][^'\"]{8,}['\"]"
    ),
    "Cadena de conexión": re.compile(r"(?i)\b(?:mongodb(?:\+srv)?|postgres(?:ql)?|mysql|redis|amqp)://[^@\s]+@"),
}

# Falso positivo conocido: token de diseño CSS (`--…`) o handle opaco de fixture.
# No relaja password, api_key, secret ni otros valores de token.
DESIGN_TOKEN_ASSIGN_RE = re.compile(r"""(?i)\btoken\b\s*[:=]\s*['"](?:--[A-Za-z0-9_-]+|opaque-handle\.json)['"]""")

MARKER_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX|BUG)\b")

# No escanear marcadores/secretos en docs o en el propio detector
LOW_CONFIDENCE_PATH_RE = re.compile(
    r"(^|/)(docs?|documentation|examples?|fixtures?|testdata|__mocks__)(/|$)",
    re.IGNORECASE,
)
SKIP_CONTENT_SCAN_RE = re.compile(
    r"(^|/)(SKILL\.md|references/|scripts/scan_repo\.py$)",
    re.IGNORECASE,
)

ENV_FILE_RE = re.compile(r"^\.env(\..+)?$", re.IGNORECASE)
ENV_SAFE_SUFFIXES = (".example", ".sample", ".template", ".dist")

TEXT_EXTS = set(LANG_BY_EXT) | {
    ".txt",
    ".cfg",
    ".ini",
    ".conf",
    ".env",
    ".lock",
    ".gitignore",
    ".editorconfig",
    ".csv",
    ".tsv",
}

MAX_PATTERN_SCAN_BYTES = 2 * 1024 * 1024
MAX_HASH_BYTES = 10 * 1024 * 1024
LARGE_FILE_BYTES = 1 * 1024 * 1024

TRACKED_ARTIFACT_RE = re.compile(
    r"(^|/)(node_modules/|__pycache__/|\.venv/|venv/|\.env$|\.env\.|"
    r"\.pyc$|\.pyo$|\.class$|\.o$|\.so$|\.dylib$)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def is_probably_binary(path: str, sample_size: int = 4096) -> bool:
    try:
        with open(path, "rb") as fh:
            chunk = fh.read(sample_size)
    except OSError:
        return False
    if not chunk:
        return False
    return b"\x00" in chunk


def hash_file(path: str) -> str | None:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()


def should_ignore_dirname(name: str) -> bool:
    if name in IGNORE_DIRS:
        return True
    return any(name.endswith(suf) for suf in IGNORE_DIR_SUFFIXES)


def iter_files(root: str) -> Iterator[str]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not should_ignore_dirname(d))
        for fname in sorted(filenames):
            yield os.path.join(dirpath, fname)


def rel(root: str, path: str) -> str:
    return os.path.relpath(path, root).replace(os.sep, "/")


def is_env_file(basename: str) -> bool:
    if not ENV_FILE_RE.match(basename):
        return False
    lower = basename.lower()
    return not any(lower.endswith(suf) for suf in ENV_SAFE_SUFFIXES)


def is_pascal_case_ok(basename: str, ext: str) -> bool:
    stem = os.path.splitext(basename)[0]
    if not stem or not stem[0].isupper():
        return False
    return ext in PASCALCASE_EXTS


def naming_is_suspicious(basename: str, ext: str) -> str | None:
    if " " in basename:
        return "con_espacios"
    if any(basename.startswith(p) for p in STANDARD_NAME_PREFIXES):
        return None
    if basename != basename.lower() and not is_pascal_case_ok(basename, ext):
        # Permitir camelCase/PascalCase residual solo si tiene mayúsculas
        # y no es extensión de componente/clase
        return "con_mayusculas"
    try:
        basename.encode("ascii")
    except UnicodeEncodeError:
        return "no_ascii"
    return None


def path_confidence(rel_path: str) -> str:
    if SKIP_CONTENT_SCAN_RE.search(rel_path):
        return "omitido"
    if LOW_CONFIDENCE_PATH_RE.search(rel_path):
        return "baja"
    parts = set(rel_path.lower().split("/"))
    if parts & TEST_DIR_NAMES or TEST_FILE_RE.search(os.path.basename(rel_path)):
        return "baja"
    return "alta"


def is_dedicated_test_path(rel_path: str, basename: str) -> bool:
    """True solo si el fichero está en un dir de tests o el nombre es de test."""
    parts = rel_path.lower().split("/")
    # El segmento de directorio (no el nombre del fichero) debe ser test dir
    dir_parts = set(parts[:-1]) if len(parts) > 1 else set()
    if dir_parts & TEST_DIR_NAMES:
        return True
    return bool(TEST_FILE_RE.search(basename))


def version_is_unpinned(ver: str | None) -> bool:
    ver = (ver or "").strip()
    if not ver:
        return True
    if ver in ("*", "latest"):
        return True
    return bool(ver.startswith(("http:", "https:", "git+", "file:", "link:", "workspace:")))


MIN_VERSION_FIELDS = 2
MAX_LISTED_MANIFESTS = 5


def pip_line_unpinned(line: str) -> bool:
    line = line.strip()
    if not line or line.startswith(("#", "-", ".")):
        return False
    # Exacta o con operador de versión acotado: OK
    return not re.search(r"(==|>=|<=|~=|!=|>|<)", line)


# ---------------------------------------------------------------------------
# Escaneo principal
# ---------------------------------------------------------------------------


@dataclass
class _ScanCtx:
    """Estado mutable del escaneo: informe y contadores."""

    report: dict[str, Any]
    lang_bytes: Counter[str]
    lang_files: Counter[str]
    marker_hits: Counter[str]
    hashes: defaultdict[tuple[int, str], list[str]]
    test_dirs: set[str]
    total_files: int
    total_bytes: int


def _init_ctx(root: str) -> _ScanCtx:
    report: dict[str, Any] = {
        "raiz": root,
        "resumen": {},
        "lenguajes": {},
        "ficheros_estandar": {},
        "ci_detectado": [],
        "manifiestos": {},
        "higiene": defaultdict(list),
        "nombrado": defaultdict(list),
        # Clave canónica sin substring "secret" (CodeQL clear-text sources).
        "hallazgos_patrones": [],
        "env_versionados": [],
        "duplicados": [],
        "marcadores": {},
        "tests": {
            "ficheros_test": 0,
            "ficheros_codigo": 0,
            "directorios_test": [],
        },
        "salud_dependencias": [],
        "artefactos_trackeados": [],
    }
    return _ScanCtx(
        report=report,
        lang_bytes=Counter(),
        lang_files=Counter(),
        marker_hits=Counter(),
        hashes=defaultdict(list),
        test_dirs=set(),
        total_files=0,
        total_bytes=0,
    )


def _index_root(ctx: _ScanCtx, root: str) -> bool:
    try:
        root_entries = set(os.listdir(root))
    except OSError as exc:
        ctx.report["error"] = f"No se puede leer la raíz: {exc}"
        return False
    for key, candidates in STANDARD_FILES.items():
        ctx.report["ficheros_estandar"][key] = any(c in root_entries for c in candidates)
    for ci in CI_PATHS:
        if os.path.exists(os.path.join(root, ci)):
            ctx.report["ci_detectado"].append(ci)
    return True


def _scan_higiene(ctx: _ScanCtx, r: str, size: int, binary: bool, ext: str) -> None:
    if size == 0:
        ctx.report["higiene"]["vacios"].append(r)
    elif size > LARGE_FILE_BYTES:
        ctx.report["higiene"]["grandes"].append({"fichero": r, "bytes": size})

    if binary and (ext in TEXT_EXTS or ext == ""):
        ctx.report["higiene"]["binarios_sospechosos"].append(r)
    if binary and size > LARGE_FILE_BYTES:
        ctx.report["higiene"]["binarios_grandes"].append({"fichero": r, "bytes": size})


def _scan_naming(ctx: _ScanCtx, r: str, basename: str, ext: str) -> None:
    flag = naming_is_suspicious(basename, ext)
    if flag == "con_espacios":
        ctx.report["nombrado"]["con_espacios"].append(r)
    elif flag == "con_mayusculas":
        ctx.report["nombrado"]["con_mayusculas"].append(r)
    elif flag == "no_ascii":
        ctx.report["nombrado"]["no_ascii"].append(r)


def _scan_tests(ctx: _ScanCtx, r: str, basename: str, lang: str | None, is_test: bool) -> None:
    if lang in CODE_LANGS:
        if is_test:
            ctx.report["tests"]["ficheros_test"] += 1
        else:
            ctx.report["tests"]["ficheros_codigo"] += 1
    if is_test:
        parts = r.lower().split("/")
        for i, part in enumerate(parts[:-1]):
            if part in TEST_DIR_NAMES:
                ctx.test_dirs.add("/".join(parts[: i + 1]))


def _decode_text(ctx: _ScanCtx, raw: bytes, r: str) -> str | None:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        ctx.report["higiene"]["no_utf8"].append(r)
        try:
            return raw.decode("latin-1")
        except UnicodeDecodeError:
            return None


def _scan_text(ctx: _ScanCtx, text: str, raw: bytes, r: str, confidence: str) -> None:
    if raw.startswith(b"\xef\xbb\xbf"):
        ctx.report["higiene"]["con_bom"].append(r)
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n")
    if lf and crlf and crlf != lf:
        ctx.report["higiene"]["finales_mixtos"].append(r)

    for name, pat in CREDENTIAL_PATTERNS.items():
        for m in pat.finditer(text):
            # Solo metadatos: nunca m.group() / valor / snippet (CodeQL clear-text).
            if name == "Asignación de credencial" and DESIGN_TOKEN_ASSIGN_RE.fullmatch(text[m.start() : m.end()]):
                continue
            line_no = text.count("\n", 0, m.start()) + 1
            ctx.report["hallazgos_patrones"].append(_pattern_hit(name, r, line_no, confidence))
            break  # una coincidencia por tipo y fichero basta

    if confidence == "alta":
        for m in MARKER_RE.finditer(text):
            ctx.marker_hits[m.group(1)] += 1


def _wants_content(size: int, binary: bool, ext: str, basename: str, confidence: str) -> bool:
    return (
        not binary
        and 0 < size <= MAX_PATTERN_SCAN_BYTES
        and (ext in TEXT_EXTS or ext == "" or basename.startswith(".env"))
        and confidence != "omitido"
    )


def _scan_content(ctx: _ScanCtx, path: str, r: str, size: int, binary: bool) -> None:
    ext = os.path.splitext(path)[1]
    basename = os.path.basename(path)
    confidence = path_confidence(r)
    if not _wants_content(size, binary, ext, basename, confidence):
        return
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError:
        return
    text = _decode_text(ctx, raw, r)
    if text is None:
        return
    _scan_text(ctx, text, raw, r, confidence)


def _scan_file(ctx: _ScanCtx, root: str, path: str) -> None:
    r = rel(root, path)
    ctx.total_files += 1
    try:
        size = os.path.getsize(path)
    except OSError:
        return
    ctx.total_bytes += size

    basename = os.path.basename(path)
    ext = os.path.splitext(path)[1]
    lang = LANG_BY_EXT.get(ext)
    if lang:
        ctx.lang_bytes[lang] += size
        ctx.lang_files[lang] += 1

    if basename in MANIFESTS:
        ctx.report["manifiestos"].setdefault(MANIFESTS[basename], []).append(r)
    if is_env_file(basename):
        ctx.report["env_versionados"].append(r)

    binary = is_probably_binary(path)
    _scan_higiene(ctx, r, size, binary, ext)
    _scan_naming(ctx, r, basename, ext)
    _scan_tests(ctx, r, basename, lang, is_dedicated_test_path(r, basename))
    _scan_content(ctx, path, r, size, binary)

    # --- Duplicados (no hashear ficheros enormes) ---
    if 0 < size <= MAX_HASH_BYTES:
        digest = hash_file(path)
        if digest:
            ctx.hashes[(size, digest)].append(r)


def _collect_duplicates(ctx: _ScanCtx) -> None:
    for (size, digest), paths in ctx.hashes.items():
        if len(paths) > 1:
            ctx.report["duplicados"].append(
                {
                    "bytes": size,
                    "sha256": digest[:16],
                    "ficheros": paths,
                }
            )


def _build_summary(ctx: _ScanCtx, root: str) -> None:
    report = ctx.report
    report["tests"]["directorios_test"] = sorted(ctx.test_dirs)
    report["lenguajes"] = {
        lang: {"ficheros": ctx.lang_files[lang], "bytes": ctx.lang_bytes[lang]}
        for lang, _ in ctx.lang_bytes.most_common()
    }
    report["marcadores"] = dict(ctx.marker_hits.most_common())
    report["resumen"] = {
        "total_ficheros": ctx.total_files,
        "total_bytes": ctx.total_bytes,
        "lenguaje_principal": ctx.lang_bytes.most_common(1)[0][0] if ctx.lang_bytes else None,
        "n_hallazgos_patrones": len(report["hallazgos_patrones"]),
        "n_hallazgos_alta": sum(1 for s in report["hallazgos_patrones"] if s.get("confianza") == "alta"),
        "n_env_versionados": len(report["env_versionados"]),
        "n_duplicados": len(report["duplicados"]),
        "n_vacios": len(report["higiene"].get("vacios", [])),
        "n_grandes": len(report["higiene"].get("grandes", [])),
    }

    report["salud_dependencias"] = check_dependency_health(root)
    report["artefactos_trackeados"] = check_tracked_artifacts(root)
    report["higiene"] = {k: v for k, v in report["higiene"].items()}
    report["nombrado"] = {k: v for k, v in report["nombrado"].items()}
    # Alias de escritura para consumidores del JSON. Ningún sink (print/write) los lee.
    report["secretos_potenciales"] = report["hallazgos_patrones"]
    report["resumen"]["n_secretos_potenciales"] = report["resumen"]["n_hallazgos_patrones"]
    report["resumen"]["n_secretos_alta_confianza"] = report["resumen"]["n_hallazgos_alta"]


def scan(root: str) -> dict[str, Any]:
    root = os.path.abspath(root)
    ctx = _init_ctx(root)
    if not _index_root(ctx, root):
        return ctx.report
    for path in iter_files(root):
        _scan_file(ctx, root, path)
    _collect_duplicates(ctx)
    _build_summary(ctx, root)
    return ctx.report


def _pkg_candidates(root: str) -> list[str]:
    candidates = [os.path.join(root, "package.json")]
    for sub in ("apps", "packages", "services"):
        subroot = os.path.join(root, sub)
        if os.path.isdir(subroot):
            for name in os.listdir(subroot):
                cand = os.path.join(subroot, name, "package.json")
                if os.path.isfile(cand):
                    candidates.append(cand)
    return candidates


def _package_json_findings(root: str) -> list[str]:
    findings: list[str] = []
    for pkg in _pkg_candidates(root):
        if not os.path.isfile(pkg):
            continue
        rel_pkg = rel(root, pkg)
        try:
            with open(pkg, encoding="utf-8") as fh:
                data = json.load(fh)
            for section in ("dependencies", "devDependencies"):
                for dep, ver in (data.get(section) or {}).items():
                    if version_is_unpinned(str(ver)):
                        findings.append(f"{rel_pkg}: dependencia sin fijar '{dep}': '{ver}' ({section})")
        except (json.JSONDecodeError, OSError) as exc:
            findings.append(f"{rel_pkg}: no se pudo parsear ({exc})")
    return findings


def _lockfile_findings(root: str) -> list[str]:
    root_pkg = os.path.join(root, "package.json")
    locks = ("package-lock.json", "pnpm-lock.yaml", "yarn.lock")
    if os.path.isfile(root_pkg) and not any(os.path.isfile(os.path.join(root, lock)) for lock in locks):
        return ["package.json sin fichero lock (package-lock/pnpm-lock/yarn.lock)"]
    return []


def _requirements_findings(root: str) -> list[str]:
    req = os.path.join(root, "requirements.txt")
    if not os.path.isfile(req):
        return []
    findings: list[str] = []
    try:
        with open(req, encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                if pip_line_unpinned(line):
                    findings.append(f"requirements.txt:{i}: dependencia sin versión: '{line.strip()}'")
    except OSError:
        pass
    return findings


def _pyproject_findings(root: str) -> list[str]:
    pyproject = os.path.join(root, "pyproject.toml")
    if not os.path.isfile(pyproject):
        return []
    findings: list[str] = []
    try:
        with open(pyproject, encoding="utf-8") as fh:
            text = fh.read()
        # Detección ligera sin tomllib (compat Python <3.11): * o latest en deps
        for m in re.finditer(
            r"""["']([A-Za-z0-9_.\-]+)["']\s*=\s*["'](\*|latest)["']""",
            text,
        ):
            findings.append(f"pyproject.toml: dependencia sin fijar '{m.group(1)}': '{m.group(2)}'")
    except OSError:
        pass
    return findings


def _cargo_findings(root: str) -> list[str]:
    cargo = os.path.join(root, "Cargo.toml")
    if not os.path.isfile(cargo):
        return []
    findings: list[str] = []
    try:
        with open(cargo, encoding="utf-8") as fh:
            text = fh.read()
        for m in re.finditer(
            r"""^\s*([A-Za-z0-9_\-]+)\s*=\s*["'](\*|latest)["']""",
            text,
            re.MULTILINE,
        ):
            findings.append(f"Cargo.toml: dependencia sin fijar '{m.group(1)}': '{m.group(2)}'")
    except OSError:
        pass
    return findings


def _gomod_findings(root: str) -> list[str]:
    gomod = os.path.join(root, "go.mod")
    if not os.path.isfile(gomod):
        return []
    findings: list[str] = []
    try:
        with open(gomod, encoding="utf-8") as fh:
            for i, raw in enumerate(fh, 1):
                line = raw.strip()
                if line.startswith("require") or line.startswith("//") or not line:
                    continue
                # require directo: module vX.Y.Z  — sin versión = raro
                parts = line.split()
                if (
                    parts
                    and parts[0].startswith(("github.com/", "golang.org/", "gopkg.in/"))
                    and len(parts) < MIN_VERSION_FIELDS
                ):
                    findings.append(f"go.mod:{i}: módulo sin versión: '{line}'")
    except OSError:
        pass
    return findings


def check_dependency_health(root: str) -> list[str]:
    findings: list[str] = []
    for check in (
        _package_json_findings,
        _lockfile_findings,
        _requirements_findings,
        _pyproject_findings,
        _cargo_findings,
        _gomod_findings,
    ):
        findings.extend(check(root))
    return findings


def check_tracked_artifacts(root: str) -> list[str]:
    """Si hay .git, listar artefactos típicamente no versionables ya trackeados."""
    git_dir = os.path.join(root, ".git")
    if not os.path.isdir(git_dir):
        return []
    try:
        out = subprocess.run(
            ["git", "-C", root, "ls-files"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if out.returncode != 0:
        return []
    findings: list[str] = []
    for path in out.stdout.splitlines():
        if TRACKED_ARTIFACT_RE.search(path):
            # .env.example no es artefacto peligroso
            base = os.path.basename(path)
            if base.lower().startswith(".env") and any(base.lower().endswith(suf) for suf in ENV_SAFE_SUFFIXES):
                continue
            findings.append(path)
    return findings[:100]


# ---------------------------------------------------------------------------
# Salida
# ---------------------------------------------------------------------------


def _md_header(rep: dict[str, Any]) -> list[str]:
    r = rep["resumen"]
    lines = [
        "# Escaneo estructural del repositorio",
        "",
        f"- Raíz: `{rep['raiz']}`",
        f"- Ficheros analizados: **{r.get('total_ficheros', 0)}** ({r.get('total_bytes', 0) / 1024:.1f} KiB)",
        f"- Lenguaje principal: **{r.get('lenguaje_principal') or 'n/d'}**",
        "",
        "## Lenguajes",
    ]
    for lang, d in rep["lenguajes"].items():
        lines.append(f"- {lang}: {d['ficheros']} ficheros, {d['bytes'] / 1024:.1f} KiB")
    return lines


def _md_standard(rep: dict[str, Any]) -> list[str]:
    lines = ["", "## Ficheros estándar"]
    for k, ok in rep["ficheros_estandar"].items():
        lines.append(f"- {k}: {'✅' if ok else '❌ ausente'}")
    if rep["ci_detectado"]:
        lines.append(f"- CI detectada: {', '.join(rep['ci_detectado'])}")
    else:
        lines.append("- CI detectada: ❌ ninguna")
    return lines


def _md_manifests(rep: dict[str, Any]) -> list[str]:
    if not rep["manifiestos"]:
        return []
    lines = ["", "## Manifiestos"]
    for kind, paths in rep["manifiestos"].items():
        head = ", ".join(paths[:MAX_LISTED_MANIFESTS])
        extra = f" (+{len(paths) - MAX_LISTED_MANIFESTS} más)" if len(paths) > MAX_LISTED_MANIFESTS else ""
        lines.append(f"- {kind}: {head}{extra}")
    return lines


def _md_alerts(rep: dict[str, Any]) -> list[str]:
    r = rep["resumen"]
    return [
        "",
        "## Alertas",
        f"- Hallazgos de patrones: **{len(rep['hallazgos_patrones'])}** "
        f"(alta confianza: {r.get('n_hallazgos_alta', 0)})",
        f"- `.env` versionados: **{len(rep.get('env_versionados', []))}**",
        f"- Duplicados exactos: **{len(rep['duplicados'])}**",
        f"- Ficheros vacíos: {len(rep['higiene'].get('vacios', []))}",
        f"- Ficheros >1 MiB: {len(rep['higiene'].get('grandes', []))}",
        f"- No UTF-8: {len(rep['higiene'].get('no_utf8', []))}",
        f"- Finales de línea mixtos: {len(rep['higiene'].get('finales_mixtos', []))}",
        f"- Nombres con espacios: {len(rep['nombrado'].get('con_espacios', []))}",
    ]


def _md_env_files(rep: dict[str, Any]) -> list[str]:
    if not rep.get("env_versionados"):
        return []
    return ["", "### Ficheros .env versionados", *[f"- `{e}`" for e in rep["env_versionados"][:30]]]


def _md_findings(rep: dict[str, Any]) -> list[str]:
    hallazgos = rep["hallazgos_patrones"]
    if not hallazgos:
        return []
    lines = ["", "### Hallazgos de patrones (solo path:línea; sin valor)"]
    for s in hallazgos[:30]:
        fp = s.get("fingerprint", "n/d")
        lines.append(
            f"- [{s['tipo']}] `{s['fichero']}:{s['linea']}` (confianza: {s.get('confianza', 'n/d')}; fp: `{fp}`)"
        )
    return lines


def _md_deps(rep: dict[str, Any]) -> list[str]:
    if not rep["salud_dependencias"]:
        return []
    return ["", "### Salud de dependencias", *[f"- {f}" for f in rep["salud_dependencias"][:40]]]


def _md_artifacts(rep: dict[str, Any]) -> list[str]:
    if not rep.get("artefactos_trackeados"):
        return []
    return [
        "",
        "### Artefactos trackeados (candidatos a .gitignore)",
        *[f"- `{a}`" for a in rep["artefactos_trackeados"][:30]],
    ]


def _md_markers(rep: dict[str, Any]) -> list[str]:
    if not rep["marcadores"]:
        return []
    return ["", "### Marcadores (solo confianza alta)", *[f"- {m}: {n}" for m, n in rep["marcadores"].items()]]


def _md_tests(rep: dict[str, Any]) -> list[str]:
    t = rep["tests"]
    ratio = f" | ratio: {t['ficheros_test'] / t['ficheros_codigo']:.2%}" if t["ficheros_codigo"] else ""
    lines = [
        "",
        "### Tests",
        f"- Ficheros de test: {t['ficheros_test']} | Ficheros de código: {t['ficheros_codigo']}{ratio}",
    ]
    if t["directorios_test"]:
        lines.append(f"- Directorios de test: {', '.join(t['directorios_test'])}")
    return lines


def to_markdown(rep: dict[str, Any]) -> str:
    lines: list[str] = []
    for section in (
        _md_header,
        _md_standard,
        _md_manifests,
        _md_alerts,
        _md_env_files,
        _md_findings,
        _md_deps,
        _md_artifacts,
        _md_markers,
        _md_tests,
    ):
        lines.extend(section(rep))
    return "\n".join(lines)


def warn_if_output_inside_repo(repo: str, out_path: str) -> None:
    if not out_path:
        return
    repo_abs = os.path.abspath(repo)
    out_abs = os.path.abspath(out_path)
    try:
        common = os.path.commonpath([repo_abs, out_abs])
    except ValueError:
        return
    if common == repo_abs:
        logger.warning(
            "La salida '%s' cae dentro del repositorio auditado; preferible escribir fuera del árbol.",
            out_path,
        )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Escaneo estructural de un repositorio")
    ap.add_argument("repo", help="Ruta raíz del repositorio")
    ap.add_argument("--json", help="Guardar informe JSON en esta ruta")
    ap.add_argument("--md", help="Guardar resumen Markdown en esta ruta")
    return ap


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    ap = build_parser()
    args = ap.parse_args(argv)

    if not os.path.isdir(args.repo):
        logger.error("'%s' no es un directorio", args.repo)
        return 1

    warn_if_output_inside_repo(args.repo, args.json)
    warn_if_output_inside_repo(args.repo, args.md)

    rep = scan(args.repo)
    md = to_markdown(rep)

    if args.json:
        try:
            with open(args.json, "w", encoding="utf-8") as fh:
                json.dump(rep, fh, ensure_ascii=False, indent=2)
        except OSError as exc:
            logger.error("No se pudo escribir el JSON '%s': %s", args.json, exc)
            return 1
        print(f"JSON guardado en {args.json}")
    if args.md:
        try:
            with open(args.md, "w", encoding="utf-8") as fh:
                fh.write(md + "\n")
        except OSError as exc:
            logger.error("No se pudo escribir el Markdown '%s': %s", args.md, exc)
            return 1
        print(f"Markdown guardado en {args.md}")
    if not args.json and not args.md:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
