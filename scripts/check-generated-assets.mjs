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
  {
    label: "Readable preview render",
    file: "renders/organic-growth-vessel-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/voronoi-light-shell.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/voronoi-light-shell.glb",
  },
  {
    label: "Transparent render",
    file: "renders/voronoi-light-shell.png",
  },
  {
    label: "Readable preview render",
    file: "renders/voronoi-light-shell-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/luminous-seed-vessel.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/luminous-seed-vessel.glb",
  },
  {
    label: "Transparent render",
    file: "renders/luminous-seed-vessel.png",
  },
  {
    label: "Readable preview render",
    file: "renders/luminous-seed-vessel-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/tidal-coral-helix.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/tidal-coral-helix.glb",
  },
  {
    label: "Transparent render",
    file: "renders/tidal-coral-helix.png",
  },
  {
    label: "Readable preview render",
    file: "renders/tidal-coral-helix-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/manta-bloom-shell.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/manta-bloom-shell.glb",
  },
  {
    label: "Transparent render",
    file: "renders/manta-bloom-shell.png",
  },
  {
    label: "Readable preview render",
    file: "renders/manta-bloom-shell-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/spore-current-lantern.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/spore-current-lantern.glb",
  },
  {
    label: "Transparent render",
    file: "renders/spore-current-lantern.png",
  },
  {
    label: "Readable preview render",
    file: "renders/spore-current-lantern-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/kelp-pulse-torus.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/kelp-pulse-torus.glb",
  },
  {
    label: "Transparent render",
    file: "renders/kelp-pulse-torus.png",
  },
  {
    label: "Readable preview render",
    file: "renders/kelp-pulse-torus-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/visceral-tide-knot.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/visceral-tide-knot.glb",
  },
  {
    label: "Transparent render",
    file: "renders/visceral-tide-knot.png",
  },
  {
    label: "Readable preview render",
    file: "renders/visceral-tide-knot-preview.png",
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
  console.log("blender --background --python offline/generate_voronoi_light_shell.py");
  console.log("Or, on the Mac mini GUI workflow: npm run watcher:start && npm run job:all");
  process.exitCode = 1;
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
