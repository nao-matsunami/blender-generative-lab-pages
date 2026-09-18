import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const jobsDir = path.join(rootDir, "blender-jobs");
const statusPath = path.join(jobsDir, "watcher.status.txt");
const restartCommand = `exec(open(${JSON.stringify(path.join(rootDir, "offline/gui_job_watcher.py"))}).read())`;

const files = await fs.readdir(jobsDir);
const pending = files.filter((file) => file.endsWith(".job.py")).sort();
const running = files.filter((file) => file.endsWith(".running")).sort();

let status = "missing";
let ageSeconds = Infinity;
try {
  const stat = await fs.stat(statusPath);
  status = (await fs.readFile(statusPath, "utf8")).trim() || "empty";
  ageSeconds = Math.floor((Date.now() - stat.mtimeMs) / 1000);
} catch {
  // A missing status file means Blender has not started the watcher yet.
}

console.log(`Watcher status: ${status}`);
console.log(`Status age: ${Number.isFinite(ageSeconds) ? `${ageSeconds}s` : "unknown"}`);
console.log(`Pending jobs: ${pending.length}`);
for (const file of pending) console.log(`  ${file}`);
console.log(`Running jobs: ${running.length}`);
for (const file of running) console.log(`  ${file}`);

if (ageSeconds > 15 || status === "missing") {
  console.log("\nWatcher is stale or stopped. Run this in Blender's Python Console:");
  console.log(restartCommand);
} else if (pending.length > 0 && running.length === 0) {
  console.log("\nWatcher is fresh; pending jobs should start within two seconds.");
} else {
  console.log("\nWatcher is healthy.");
}
