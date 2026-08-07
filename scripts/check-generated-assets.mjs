import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

const expected = [
  {
    label: "STL print export",
    file: "exports/stl/organic-growth-vessel.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/organic-growth-vessel.glb",
  },
  {
    label: "Transparent render",
    file: "renders/organic-growth-vessel.png",
  },
];

let failed = false;

for (const item of expected) {
  const absolutePath = path.join(rootDir, item.file);
  try {
    const stat = await fs.stat(absolutePath);
    if (!stat.isFile() || stat.size === 0) {
      failed = true;
      console.log(`MISSING ${item.label}: ${item.file}`);
      continue;
    }
    console.log(`OK ${item.label}: ${item.file} (${formatBytes(stat.size)})`);
  } catch {
    failed = true;
    console.log(`MISSING ${item.label}: ${item.file}`);
  }
}

if (failed) {
  console.log("");
  console.log("Run Blender first:");
  console.log("blender --background --python offline/generate_organic_growth_vessel.py");
  process.exitCode = 1;
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
