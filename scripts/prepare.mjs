import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);

try {
  require.resolve("husky");
} catch {
  console.log("husky is not installed; skipping development hooks");
  process.exit(0);
}

execFileSync("husky", { stdio: "inherit" });
