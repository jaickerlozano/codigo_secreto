import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";

const [commandName, ...commandArguments] = process.argv.slice(2);
const supportedCommands = new Set(["vite", "vitest"]);

if (!commandName || !supportedCommands.has(commandName)) {
  console.error("Expected a local vite or vitest command.");
  process.exit(1);
}

const require = createRequire(import.meta.url);
let executable;

try {
  const packageJsonPath = require.resolve(`${commandName}/package.json`);
  const packageJson = JSON.parse(readFileSync(packageJsonPath, "utf8"));
  const binPath =
    typeof packageJson.bin === "string" ? packageJson.bin : packageJson.bin?.[commandName];

  if (!binPath) {
    throw new Error(`${commandName} does not declare a compatible executable`);
  }

  executable = resolve(dirname(packageJsonPath), binPath);
} catch (error) {
  console.error(`Unable to resolve the installed ${commandName} executable: ${error.message}`);
  process.exit(1);
}

const result = spawnSync(process.execPath, [executable, ...commandArguments], {
  stdio: "inherit",
  env: { ...process.env, LOCAL_NO_DOTENV: "1" },
});

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}

process.exit(result.status ?? 1);
