import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";

const require = createRequire(import.meta.url);
let executable;

try {
  const packageJsonPath = require.resolve("openapi-typescript/package.json");
  const packageJson = JSON.parse(readFileSync(packageJsonPath, "utf8"));
  const binPath =
    typeof packageJson.bin === "string"
      ? packageJson.bin
      : packageJson.bin?.["openapi-typescript"];

  if (!binPath) {
    throw new Error("openapi-typescript does not declare a compatible executable");
  }

  executable = resolve(dirname(packageJsonPath), binPath);
} catch (error) {
  console.error(`Unable to resolve the installed openapi-typescript executable: ${error.message}`);
  process.exit(1);
}

const apiBaseUrl = (process.env.VITE_API_URL?.trim() || "http://localhost:8000").replace(
  /\/+$/,
  "",
);
const schemaUrl = `${apiBaseUrl}/api/schema/`;
const schemaSource = process.env.OPENAPI_SCHEMA_PATH?.trim() || schemaUrl;
const result = spawnSync(
  process.execPath,
  [executable, schemaSource, "-o", "src/api/schema.d.ts"],
  { stdio: "inherit", env: process.env },
);

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}

process.exit(result.status ?? 1);
