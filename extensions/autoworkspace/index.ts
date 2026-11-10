import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

const ALLOWED_SKILLS = new Set([
  "plan-specification",
  "plan-validators",
  "role-back",
  "role-front",
  "role-design",
  "role-clean-code",
  "project-autoworkspace",
]);
const OUTPUT_CAP = 50 * 1024;

function allowedCwd(candidate: string, parent: string): boolean {
  const resolved = path.resolve(candidate);
  const root = path.resolve(parent);
  return (
    resolved === root ||
    resolved.startsWith(root + path.sep) ||
    resolved.startsWith("/tmp/autoworkspace-")
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

export default function autoworkspace(pi: ExtensionAPI) {
  pi.registerCommand("aw-status", {
    description: "Confirm that the autoworkspace Pi extension is loaded",
    async handler(_args, ctx) {
      ctx.ui.notify("autoworkspace extension loaded", "info");
    },
  });

  pi.registerTool({
    name: "aw_subagent",
    label: "Autoworkspace subagent",
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
      if (!ALLOWED_SKILLS.has(params.skill)) {
        return {
          content: [{ type: "text", text: "skill not allowed" }],
          isError: true,
        };
      }
      const cwd = path.resolve(params.cwd ?? ctx.cwd);
      if (!allowedCwd(cwd, ctx.cwd)) {
        return {
          content: [
            {
              type: "text",
              text: "cwd outside authorized workspace/worktree roots",
            },
          ],
          isError: true,
        };
      }
      const tools = ["read", "grep", "find", "ls"];
      if (params.write) tools.push("write", "edit");
      if (params.allow_bash) tools.push("bash");
      // Follow symlink when installed as ~/.pi/agent/extensions/autoworkspace.ts
      const extensionDir = path.dirname(fs.realpathSync(fileURLToPath(import.meta.url)));
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
      const timeoutMs = (params.timeout_seconds ?? 300) * 1000;
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
        detail: parseError || stderr.slice(0, 2000),
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
