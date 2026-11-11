/**
 * path-guard — protects sensitive paths OUTSIDE ~/Work/
 *
 * Inside ~/Work/ nothing is blocked (the operator edits there).
 *
 * Outside ~/Work/:
 *   - Hard block: ~/.ssh, ~/.gnupg, ~/.config/hypr, ~/.pi/agent/extensions
 *     (self-protection), ~/.pi/agent/auth.json, ~/.aws, ~/.kube, the machineroom
 *     runtime, the home root, and any path with .env, .git or node_modules.
 *   - Confirmation (UI) or block (no UI): settings.json, mcp.json, AGENTS.md,
 *     ~/.bashrc, ~/.bash_aliases, ~/.profile, ~/.config/git/ignore,
 *     ~/.config/gh/hosts.yml.
 *   - Fail-closed (D1/H1): any other path outside ~/Work/ that is not under an
 *     explicit allowlist is never silently allowed; it asks with UI and blocks
 *     without.
 *
 * `decidePath` is the pure decision surface (unit-testable through Node). The
 * event handler only maps its verdict back to the Pi tool pipeline.
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { resolve, sep } from "node:path";
import { homedir } from "node:os";

export type Verdict = "allow" | "block" | "confirm";

export interface PathDecision {
  verdict: Verdict;
  reason?: string;
}

export interface PathGuardOptions {
  home?: string;
  work?: string;
  hasUI?: boolean;
  allowPrefixes?: string[];
}

const HARD_DIRS = [".ssh", ".gnupg", ".machineroom", ".aws", ".kube"];
const HARD_SEGMENTS = [".env", ".git", "node_modules"];
const CONFIRM_FILES = [
  [".pi", "agent", "settings.json"],
  [".pi", "agent", "mcp.json"],
  [".pi", "agent", "AGENTS.md"],
  [".bashrc"],
  [".bash_aliases"],
  [".profile"],
  [".config", "git", "ignore"],
  [".config", "gh", "hosts.yml"],
];
const DEFAULT_ALLOW_PREFIXES = ["/tmp/machineroom-", "/tmp/test-", "/tmp/ai-"];

export function decidePath(
  requested: string,
  options: PathGuardOptions = {}
): PathDecision {
  const home = options.home ?? homedir();
  const work = options.work ?? resolve(home, "Work");
  const hasUI = options.hasUI ?? false;
  const allowPrefixes = options.allowPrefixes ?? DEFAULT_ALLOW_PREFIXES;

  const expand = (p: string) =>
    p === "~" ? home : p.startsWith("~/") ? resolve(home, p.slice(2)) : p;
  const target = resolve(expand(requested));

  const isInsideWork = (a: string) => a === work || a.startsWith(work + sep);
  if (isInsideWork(target)) return { verdict: "allow" };

  if (allowPrefixes.some((prefix) => target.startsWith(resolve(prefix)))) {
    return { verdict: "allow" };
  }

  const hardFiles = [resolve(home, ".pi", "agent", "auth.json")];
  const hardDirs = [
    ...HARD_DIRS.map((dir) => resolve(home, dir)),
    resolve(home, ".pi", "agent", "extensions"),
    resolve(home, ".config", "hypr"),
  ];
  const confirmFiles = new Set(
    CONFIRM_FILES.map((parts) => resolve(home, ...parts))
  );

  const block = (reason: string): PathDecision => ({
    verdict: "block",
    reason,
  });
  const confirm = (reason: string): PathDecision =>
    hasUI ? { verdict: "confirm", reason } : block(`${reason} (no UI)`);

  if (target === home) {
    return block("refusing to write to the home root");
  }
  if (HARD_SEGMENTS.some((segment) => target.split(sep).includes(segment))) {
    return block(
      "protected path segment; do not retry with ~, .. or symlinks, ask the operator"
    );
  }
  if (
    hardFiles.includes(target) ||
    hardDirs.some((dir) => target === dir || target.startsWith(dir + sep))
  ) {
    return block(
      "protected path; do not retry with variants, ask the operator"
    );
  }
  if (confirmFiles.has(target)) {
    return confirm("editing a configuration file");
  }
  return confirm("path outside ~/Work requires confirmation");
}

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName !== "write" && event.toolName !== "edit")
      return undefined;
    const requested = String((event.input as any)?.path ?? "");
    const decision = decidePath(requested, { hasUI: ctx.hasUI });

    if (decision.verdict === "allow") return undefined;

    const reason = `path-guard: ${decision.reason}: ${requested}`;
    if (decision.verdict === "block") {
      if (ctx.hasUI)
        ctx.ui.notify(`Blocked protected path: ${requested}`, "warning");
      return { block: true, reason };
    }
    // confirm
    if (!ctx.hasUI) {
      return { block: true, reason: `${reason} (no UI to confirm)` };
    }
    const ok = await ctx.ui.confirm("Write outside ~/Work?", requested);
    if (!ok)
      return {
        block: true,
        reason: `path-guard: blocked by the operator: ${requested}`,
      };
    return undefined;
  });
}
