import { copyFile, mkdir, readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { spawn } from "node:child_process";
import process from "node:process";
import { clearTimeout, setTimeout } from "node:timers";
import { fileURLToPath, URL } from "node:url";

const COMMAND_TIMEOUT_MS = 180_000;
const packageRoot = resolve(fileURLToPath(new URL("..", import.meta.url)));
const repositoryRoot = resolve(packageRoot, "..", "..", "..");
const canonicalSchema = resolve(repositoryRoot, "specs", "events", "event-envelope.v1.schema.json");
const packedSchema = resolve(packageRoot, "dist", "generated", "event-envelope.v1.schema.json");
const generatedRegistry = resolve(packageRoot, "src", "generated", "active-event-registry.v1.json");
const packedRegistry = resolve(packageRoot, "dist", "generated", "active-event-registry.v1.json");
const uv = process.platform === "win32" ? "uv.exe" : "uv";
const typescriptCompiler = resolve(repositoryRoot, "node_modules", "typescript", "bin", "tsc");

async function run(command, arguments_, cwd) {
  await new Promise((resolvePromise, rejectPromise) => {
    const child = spawn(command, arguments_, {
      cwd,
      shell: false,
      stdio: "inherit",
      windowsHide: true,
    });
    const timeout = setTimeout(() => {
      child.kill();
      rejectPromise(
        new Error(`Command exceeded ${COMMAND_TIMEOUT_MS} ms: ${command} ${arguments_.join(" ")}`),
      );
    }, COMMAND_TIMEOUT_MS);
    child.once("error", (error) => {
      clearTimeout(timeout);
      rejectPromise(error);
    });
    child.once("exit", (code, signal) => {
      clearTimeout(timeout);
      if (code === 0) {
        resolvePromise();
        return;
      }
      rejectPromise(
        new Error(`Command failed (${signal ?? String(code)}): ${command} ${arguments_.join(" ")}`),
      );
    });
  });
}

await run(
  uv,
  ["run", "--locked", "--python", "3.13", "python", "-m", "tooling.contracts.generate", "--check"],
  repositoryRoot,
);
await run(process.execPath, ["scripts/clean-build.mjs"], packageRoot);
await run(process.execPath, [typescriptCompiler, "--build", "tsconfig.build.json"], packageRoot);
await mkdir(dirname(packedSchema), { recursive: true });
await Promise.all([
  copyFile(canonicalSchema, packedSchema),
  copyFile(generatedRegistry, packedRegistry),
]);

const [sourceBytes, packedBytes, registrySourceBytes, registryPackedBytes] = await Promise.all([
  readFile(canonicalSchema),
  readFile(packedSchema),
  readFile(generatedRegistry),
  readFile(packedRegistry),
]);
if (!sourceBytes.equals(packedBytes)) {
  throw new Error("Packed schema is not a byte-for-byte copy of the canonical schema");
}
if (!registrySourceBytes.equals(registryPackedBytes)) {
  throw new Error("Packed active-event registry differs from its generated source");
}
