import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const stlDir = path.join(rootDir, "exports", "stl");

let failed = false;

const stlFiles = await listFiles(stlDir, ".stl");

if (stlFiles.length === 0) {
  fail("No STL exports found. Run Blender generation first.");
}

for (const stlFile of stlFiles) {
  const slug = path.basename(stlFile, ".stl");
  const expected = [
    {
      label: "STL print export",
      file: path.join("exports", "stl", `${slug}.stl`),
    },
    {
      label: "GLB web/object export",
      file: path.join("exports", "glb", `${slug}.glb`),
    },
    {
      label: "Transparent render",
      file: path.join("renders", `${slug}.png`),
    },
    {
      label: "Readable preview render",
      file: path.join("renders", `${slug}-preview.png`),
    },
  ];

  for (const item of expected) {
    await checkFile(item);
  }
}

if (failed) {
  console.log("");
  console.log("Run Blender first:");
  console.log("On the Mac mini GUI workflow, start Blender and run:");
  console.log('exec(open("/Users/nao/Documents/Codex/2026-08-03-xr-glsl-vj/blender-generative-lab/offline/gui_job_watcher.py").read())');
  console.log("Then submit jobs with npm run job:* as needed.");
  process.exitCode = 1;
} else {
  console.log(`OK generated asset sets: ${stlFiles.length}`);
}

async function listFiles(dir, extension) {
  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    return entries
      .filter((entry) => entry.isFile() && entry.name.endsWith(extension))
      .filter((entry) => !entry.name.includes("-fallback."))
      .map((entry) => entry.name)
      .sort();
  } catch {
    return [];
  }
}

async function checkFile(item) {
  const absolutePath = path.join(rootDir, item.file);
  try {
    const stat = await fs.stat(absolutePath);
    if (!stat.isFile() || stat.size === 0) {
      fail(`MISSING ${item.label}: ${item.file}`);
      return;
    }
    console.log(`OK ${item.label}: ${item.file} (${formatBytes(stat.size)})`);
  } catch {
    fail(`MISSING ${item.label}: ${item.file}`);
  }
}

function fail(message) {
  failed = true;
  console.log(message);
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
