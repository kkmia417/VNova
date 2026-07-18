import { rm } from "node:fs/promises";
import { basename, dirname, resolve } from "node:path";
import { fileURLToPath, URL } from "node:url";

const packageRoot = resolve(fileURLToPath(new URL("..", import.meta.url)));
const outputNames = ["build", "dist"];

for (const name of outputNames) {
  const outputDirectory = resolve(packageRoot, name);
  if (dirname(outputDirectory) !== packageRoot || basename(outputDirectory) !== name) {
    throw new Error(`Refusing to clean unexpected path: ${outputDirectory}`);
  }
  await rm(outputDirectory, { recursive: true, force: true });
}
