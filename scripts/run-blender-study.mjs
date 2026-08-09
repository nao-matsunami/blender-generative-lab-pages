import { access, constants } from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";

const scriptPath = process.argv[2];

if (!scriptPath) {
  console.error("Usage: node scripts/run-blender-study.mjs offline/script.py");
  process.exit(1);
}

const candidates = [
  process.env.BLENDER_BIN,
  "blender",
  "/Applications/Blender.app/Contents/MacOS/Blender",
  "/Applications/Blender 4.5.app/Contents/MacOS/Blender",
].filter(Boolean);

const blender = await resolveBlender(candidates);

if (!blender) {
  console.error("Blender executable not found.");
  console.error("Set BLENDER_BIN, for example:");
  console.error('BLENDER_BIN="/Applications/Blender 4.5.app/Contents/MacOS/Blender" npm run blender:organic');
  process.exit(1);
}

console.log(`Using Blender: ${blender}`);
const args = ["--background", "--factory-startup", "--python", scriptPath];
const child = spawn(blender, args, {
  cwd: path.resolve(path.dirname(new URL(import.meta.url).pathname), ".."),
  stdio: "inherit",
});

child.on("exit", (code, signal) => {
  if (signal) {
    console.error(`Blender exited by signal ${signal}`);
    process.exit(1);
  }
  if (code !== 0) {
    console.error(`Blender exited with code ${code}`);
    process.exit(code || 1);
  }
});

async function resolveBlender(values) {
  for (const value of values) {
    if (value.includes("/")) {
      try {
        await access(value, constants.X_OK);
        return value;
      } catch {
        continue;
      }
    }

    const found = await commandExists(value);
    if (found) return value;
  }
  return "";
}

function commandExists(command) {
  return new Promise((resolve) => {
    const child = spawn("zsh", ["-lc", `command -v ${JSON.stringify(command)}`], { stdio: "ignore" });
    child.on("exit", (code) => resolve(code === 0));
  });
}
