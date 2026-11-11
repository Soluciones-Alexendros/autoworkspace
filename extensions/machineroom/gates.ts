/**
 * Shell gate for Pi — same policy file and decision order as the Cursor hook
 * (`extensions/machineroom/deny-list.json`, read by `.cursor/hooks/shell_gate.py`).
 *
 * Fail-closed: a missing or invalid policy answers `deny`, never `allow`.
 */
import fs from "node:fs";
import path from "node:path";

export type Permission = "deny" | "ask" | "allow";

export interface Decision {
  permission: Permission;
  user_message: string;
  agent_message: string;
}

interface Rule {
  id: string;
  pattern: RegExp;
  message: string;
}

interface Policy {
  deny: Rule[];
  network: Rule;
  helpOrVersion: RegExp;
  tmpPrefixes: string[];
  rmRf: RegExp;
}

const POLICY_RELATIVE = path.join(
  "extensions",
  "machineroom",
  "deny-list.json"
);

function toRule(raw: unknown): Rule {
  const item = raw as { id?: unknown; pattern?: unknown; message?: unknown };
  const id = String(item?.id ?? "").trim();
  const pattern = String(item?.pattern ?? "");
  const message = String(item?.message ?? "").trim();
  if (!id || !pattern || !message)
    throw new Error(`deny list rule is incomplete: ${JSON.stringify(raw)}`);
  return { id, pattern: new RegExp(pattern, "i"), message };
}

/** Load and validate the shared policy from a repository or runtime root. */
export function loadPolicy(root: string): Policy {
  const policyPath = path.join(root, POLICY_RELATIVE);
  const raw = JSON.parse(fs.readFileSync(policyPath, "utf8")) as Record<
    string,
    unknown
  >;
  const denyRaw = raw.deny;
  const allow = raw.allow as
    { helpOrVersion?: unknown; tmpPrefixes?: unknown } | undefined;
  if (!Array.isArray(denyRaw) || denyRaw.length === 0)
    throw new Error("deny list needs a non-empty deny array");
  if (
    !allow ||
    !Array.isArray(allow.tmpPrefixes) ||
    allow.tmpPrefixes.length === 0
  ) {
    throw new Error("deny list needs allow.tmpPrefixes");
  }
  const deny = denyRaw.map(toRule);
  const rmRf = deny.find((rule) => rule.id === "rm-rf");
  if (!rmRf) throw new Error("deny list must keep the 'rm-rf' rule");
  return {
    deny,
    network: toRule(raw.network),
    helpOrVersion: new RegExp(String(allow.helpOrVersion ?? ""), "i"),
    tmpPrefixes: (allow.tmpPrefixes as unknown[]).map(String),
    rmRf: rmRf.pattern,
  };
}

function allow(): Decision {
  const message =
    "Allowed by the shell gate: command matches an explicit exception.";
  return { permission: "allow", user_message: message, agent_message: message };
}

function rmRfOnlyAllowedTmp(command: string, policy: Policy): boolean {
  if (!policy.rmRf.test(command)) return false;
  const paths = command.match(/(?:^|\s)(\/[^\s;|&]+)/g);
  if (!paths) return false;
  return paths
    .map((match) => match.trim())
    .every((candidate) =>
      policy.tmpPrefixes.some((prefix) => candidate.startsWith(prefix))
    );
}

/** Decide one shell command. Same order as the Python engine: allow, deny, ask. */
export function decideCommand(command: string, policy: Policy): Decision {
  if (rmRfOnlyAllowedTmp(command, policy)) return allow();
  for (const rule of policy.deny) {
    if (rule.pattern.test(command)) {
      return {
        permission: "deny",
        user_message: `Blocked host-mutating or privileged shell: ${command.slice(0, 120)}`,
        agent_message: rule.message,
      };
    }
  }
  if (policy.network.pattern.test(command)) {
    if (policy.helpOrVersion.test(command)) return allow();
    return {
      permission: "ask",
      user_message: `Network shell requires confirmation: ${command.slice(0, 120)}`,
      agent_message: policy.network.message,
    };
  }
  return {
    permission: "ask",
    user_message: `Shell gate matched; confirm: ${command.slice(0, 120)}`,
    agent_message:
      "Command matched the host/network matcher. Prefer run_registered; ask the operator.",
  };
}

/** Fail-closed wrapper: policy errors become `deny` with an explicit reason. */
export function decideWithFallback(command: string, root: string): Decision {
  try {
    return decideCommand(command, loadPolicy(root));
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    return {
      permission: "deny",
      user_message: "Shell gate: policy unavailable.",
      agent_message: `gates.ts policy error: ${detail}. Denied; fix the deny list or use run_registered.`,
    };
  }
}
