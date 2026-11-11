import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { decideWithFallback } from "./gates.ts";

const STATUS_COMMAND = "/mr-status";
const SUBAGENT_TOOL = "mr_subagent";

/**
 * Skills the isolated subagent may load by default.
 *
 * The set is a least-privilege subset of the catalog: implementation, planning
 * and self-audit only. Host mutation (`local-*`), publishing (`project-publish`)
 * and web audits are excluded because they need explicit operator consent in the
 * coordinator session. Override with `MACHINEROOM_SUBAGENT_SKILLS=comma,list`.
 */
const DEFAULT_ALLOWED_SKILLS = [
  "plan-specification",
  "plan-validators",
  "project-machineroom",
  "role-back",
  "role-clean-code",
  "role-design",
  "role-front",
] as const;

const OUTPUT_CAP = 50 * 1024;
const DEFAULT_TIMEOUT_SECONDS = 300;

function allowedSkills(env: NodeJS.ProcessEnv = process.env): Set<string> {
  const raw = (env.MACHINEROOM_SUBAGENT_SKILLS ?? "").trim();
  const list = raw
    ? raw
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean)
    : [...DEFAULT_ALLOWED_SKILLS];
  return new Set(list);
}

function allowedCwd(candidate: string, parent: string): boolean {
  const resolved = path.resolve(candidate);
  const root = path.resolve(parent);
  return (
    resolved === root ||
    resolved.startsWith(root + path.sep) ||
    resolved.startsWith("/tmp/machineroom-")
  );
}

function finalText(events: any[]): string {
  for (let index = events.length - 1; index >= 0; index -= 1) {
    const message = events[index]?.message;
    if (
      events[index]?.type === "message_end" &&
      message?.role === "assistant"
    ) {
      const text = (message.content ?? [])
        .filter((part: any) => part?.type === "text")
        .map((part: any) => part.text)
        .join("");
      if (text.length <= OUTPUT_CAP) return text;
      return text.slice(0, OUTPUT_CAP) + "\n[output truncated]";
    }
  }
  return "";
}

function rejected(detail: string) {
  return {
    content: [{ type: "text", text: detail }],
    details: {
      outcome: "blocked",
      exitCode: null,
      output: "",
      detail: `mr_subagent input: ${detail}`,
      reconciliationRequired: false,
    },
    isError: true,
  };
}

const MATCHER =
  /\b(?:apt-get|sshd|apt|dnf|pacman|systemctl|mkfs|shutdown|reboot|iptables|nft|ufw|curl|wget|nc|ssh|scp|sudo)\b|\brm\s+-rf\b|\bdd\s+if=/i;

function policyRoot(): string {
  // Installed layout: <runtime>/extensions/machineroom/index.ts
  const extensionDir = path.dirname(
    fs.realpathSync(fileURLToPath(import.meta.url))
  );
  return path.resolve(extensionDir, "..", "..");
}

export default function machineroom(pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName !== "bash") return undefined;
    const command = String(
      (event.input as { command?: unknown })?.command ?? ""
    );
    if (!MATCHER.test(command)) return undefined;
    const decision = decideWithFallback(command, policyRoot());
    if (decision.permission === "allow") return undefined;
    if (decision.permission === "deny") {
      if (ctx.hasUI) ctx.ui.notify(decision.user_message, "warning");
      return { block: true, reason: decision.agent_message };
    }
    if (!ctx.hasUI)
      return {
        block: true,
        reason: `${decision.agent_message} (no UI to confirm)`,
      };
    const ok = await ctx.ui.confirm(
      decision.user_message,
      command.slice(0, 500)
    );
    return ok ? undefined : { block: true, reason: decision.agent_message };
  });

  pi.on("user_bash", async (event, ctx) => {
    const command = String((event as { command?: unknown })?.command ?? "");
    if (!MATCHER.test(command)) return undefined;
    const decision = decideWithFallback(command, policyRoot());
    if (decision.permission === "allow") return undefined;
    return {
      result: {
        output: `shell gate: ${decision.permission} — ${decision.agent_message}
`,
        exitCode: 1,
        cancelled: true,
        truncated: false,
      },
    };
  });

  pi.registerCommand("mr-status", {
    description: "Confirm that the machineroom Pi extension is loaded",
    async handler(_args, ctx) {
      ctx.ui.notify(`machineroom extension loaded (${STATUS_COMMAND})`, "info");
    },
  });

  pi.registerTool({
    name: SUBAGENT_TOOL,
    label: "Machineroom subagent",
    description:
      "Execute one bounded task in an isolated Pi process. The coordinator remains responsible for verification.",
    parameters: Type.Object({
      skill: Type.String(),
      task: Type.String(),
      cwd: Type.Optional(Type.String()),
      write: Type.Optional(Type.Boolean()),
      allow_bash: Type.Optional(Type.Boolean()),
      timeout_seconds: Type.Optional(
        Type.Integer({ minimum: 1, maximum: 3600 })
      ),
    }),
    async execute(_toolCallId, params, signal, _onUpdate, ctx) {
      if (!allowedSkills().has(params.skill)) {
        return rejected(`skill not allowed: ${params.skill}`);
      }
      const cwd = path.resolve(params.cwd ?? ctx.cwd);
      if (!allowedCwd(cwd, ctx.cwd)) {
        return rejected(
          `cwd outside authorized workspace/worktree roots: ${cwd}`
        );
      }
      const tools = ["read", "grep", "find", "ls"];
      if (params.write) tools.push("write", "edit");
      if (params.allow_bash) tools.push("bash");
      // Follow symlink when installed as ~/.pi/agent/extensions/machineroom.ts
      const extensionDir = path.dirname(
        fs.realpathSync(fileURLToPath(import.meta.url))
      );
      const worker = path.join(extensionDir, "agents", "worker.md");
      const args = [
        "--mode",
        "json",
        "-p",
        "--no-session",
        "--tools",
        tools.join(","),
        "--append-system-prompt",
        worker,
        `/skill:${params.skill}\n\nExecute exactly this task packet:\n${params.task}`,
      ];
      const events: any[] = [];
      const child = spawn("pi", args, {
        cwd,
        shell: false,
        detached: process.platform !== "win32",
        stdio: ["ignore", "pipe", "pipe"],
      });
      let stderr = "";
      let parseError = "";
      let timedOut = false;
      let aborted = false;
      let stdoutBuffer = "";
      const processLine = (line: string) => {
        if (!line.trim()) return;
        try {
          events.push(JSON.parse(line));
        } catch {
          parseError = "invalid Pi JSONL";
        }
      };
      child.stderr.on("data", (chunk) => {
        stderr += chunk.toString();
      });
      child.stdout.on("data", (chunk) => {
        stdoutBuffer += chunk.toString();
        const lines = stdoutBuffer.split("\n");
        stdoutBuffer = lines.pop() ?? "";
        for (const line of lines) processLine(line);
      });
      const timeoutMs =
        (params.timeout_seconds ?? DEFAULT_TIMEOUT_SECONDS) * 1000;
      const timer = setTimeout(() => {
        timedOut = true;
        if (child.pid && process.platform !== "win32")
          process.kill(-child.pid, "SIGKILL");
        else child.kill("SIGKILL");
      }, timeoutMs);
      const onAbort = () => {
        aborted = true;
        if (child.pid && process.platform !== "win32")
          process.kill(-child.pid, "SIGKILL");
        else child.kill("SIGKILL");
      };
      signal?.addEventListener("abort", onAbort, { once: true });
      const exitCode = await new Promise<number>((resolve) => {
        child.on("error", () => resolve(1));
        child.on("close", (code) => {
          if (stdoutBuffer.trim()) processLine(stdoutBuffer);
          resolve(code ?? 1);
        });
      });
      clearTimeout(timer);
      signal?.removeEventListener("abort", onAbort);
      const modelFailed = events.some((event) =>
        ["error", "aborted"].includes(event?.message?.stopReason)
      );
      const failed =
        parseError || modelFailed || timedOut || aborted || exitCode !== 0;
      const result = {
        outcome:
          timedOut || aborted ? "cancelled" : failed ? "failed" : "succeeded",
        exitCode,
        output: finalText(events),
        detail: parseError
          ? `mr_subagent parse: ${parseError}`
          : `mr_subagent execute: ${stderr.slice(0, 2000)}`,
        reconciliationRequired: timedOut || aborted,
      };
      return {
        content: [{ type: "text", text: JSON.stringify(result) }],
        details: result,
        isError: result.outcome !== "succeeded",
      };
    },
  });
}
