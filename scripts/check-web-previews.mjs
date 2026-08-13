import { promises as fs } from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputsDir = path.join(rootDir, "outputs");
const reportsDir = path.join(rootDir, "reports");
const daysDir = path.join(rootDir, "days");
const nodeBin = process.execPath;

let failed = false;

const outputFiles = (await fs.readdir(outputsDir)).filter((file) => file.endsWith(".html")).sort();
const reportFiles = new Set((await fs.readdir(reportsDir)).filter((file) => file.endsWith(".json")));

for (const file of outputFiles) {
  const htmlPath = path.join(outputsDir, file);
  const html = await fs.readFile(htmlPath, "utf8");
  const date = file.slice(0, 10);
  const label = `outputs/${file}`;

  if (!/<canvas\b/i.test(html)) {
    fail(`${label}: missing canvas preview`);
  }

  if (!/<title>.+<\/title>/i.test(html)) {
    fail(`${label}: missing title`);
  }

  if (!html.includes(`../days/${date}.html`)) {
    fail(`${label}: missing Daily report link for ${date}`);
  }

  if (!reportFiles.has(`${date}.json`)) {
    fail(`${label}: missing reports/${date}.json`);
  }

  await checkModuleScripts(html, file, label);
}

for (const reportFile of [...reportFiles].sort()) {
  const date = reportFile.replace(/\.json$/, "");
  const dayPath = path.join(daysDir, `${date}.html`);
  try {
    const stat = await fs.stat(dayPath);
    if (!stat.isFile() || stat.size === 0) fail(`days/${date}.html: missing built day page`);
  } catch {
    fail(`days/${date}.html: missing built day page`);
  }
}

if (!failed) {
  console.log(`OK web previews: ${outputFiles.length} outputs`);
}

process.exitCode = failed ? 1 : 0;

async function checkModuleScripts(html, file, label) {
  const scriptPattern = /<script\s+type=["']module["'][^>]*>([\s\S]*?)<\/script>/gi;
  let match;
  let index = 0;
  while ((match = scriptPattern.exec(html))) {
    index += 1;
    const scriptPath = path.join("/tmp", `${file.replace(/[^a-z0-9_-]/gi, "_")}_${index}.mjs`);
    await fs.writeFile(scriptPath, match[1], "utf8");
    const result = await run(nodeBin, ["--check", scriptPath]);
    if (result.code !== 0) {
      fail(`${label}: module script ${index} has syntax errors\n${result.stderr.trim()}`);
    }
  }
  if (index === 0) fail(`${label}: missing module script`);
}

function fail(message) {
  failed = true;
  console.log(`FAIL ${message}`);
}

function run(command, args) {
  return new Promise((resolve) => {
    const child = spawn(command, args, { stdio: ["ignore", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += chunk.toString(); });
    child.stderr.on("data", (chunk) => { stderr += chunk.toString(); });
    child.on("exit", (code) => resolve({ code, stdout, stderr }));
  });
}
