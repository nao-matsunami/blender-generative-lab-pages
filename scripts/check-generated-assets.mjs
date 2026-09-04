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
  {
    label: "STL print export",
    file: "exports/stl/neural-gut-bloom.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/neural-gut-bloom.glb",
  },
  {
    label: "Transparent render",
    file: "renders/neural-gut-bloom.png",
  },
  {
    label: "Readable preview render",
    file: "renders/neural-gut-bloom-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/membrane-maw-cluster.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/membrane-maw-cluster.glb",
  },
  {
    label: "Transparent render",
    file: "renders/membrane-maw-cluster.png",
  },
  {
    label: "Readable preview render",
    file: "renders/membrane-maw-cluster-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/arterial-fold-nest.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/arterial-fold-nest.glb",
  },
  {
    label: "Transparent render",
    file: "renders/arterial-fold-nest.png",
  },
  {
    label: "Readable preview render",
    file: "renders/arterial-fold-nest-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/peristaltic-coil-womb.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/peristaltic-coil-womb.glb",
  },
  {
    label: "Transparent render",
    file: "renders/peristaltic-coil-womb.png",
  },
  {
    label: "Readable preview render",
    file: "renders/peristaltic-coil-womb-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/adhesion-gut-wreath.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/adhesion-gut-wreath.glb",
  },
  {
    label: "Transparent render",
    file: "renders/adhesion-gut-wreath.png",
  },
  {
    label: "Readable preview render",
    file: "renders/adhesion-gut-wreath-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/hepatic-vessel-bloom.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/hepatic-vessel-bloom.glb",
  },
  {
    label: "Transparent render",
    file: "renders/hepatic-vessel-bloom.png",
  },
  {
    label: "Readable preview render",
    file: "renders/hepatic-vessel-bloom-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/valvular-chamber-bloom.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/valvular-chamber-bloom.glb",
  },
  {
    label: "Transparent render",
    file: "renders/valvular-chamber-bloom.png",
  },
  {
    label: "Readable preview render",
    file: "renders/valvular-chamber-bloom-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/alveolar-sac-cluster.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/alveolar-sac-cluster.glb",
  },
  {
    label: "Transparent render",
    file: "renders/alveolar-sac-cluster.png",
  },
  {
    label: "Readable preview render",
    file: "renders/alveolar-sac-cluster-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/renal-pelvis-vessel.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/renal-pelvis-vessel.glb",
  },
  {
    label: "Transparent render",
    file: "renders/renal-pelvis-vessel.png",
  },
  {
    label: "Readable preview render",
    file: "renders/renal-pelvis-vessel-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/gastric-rugae-maw.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/gastric-rugae-maw.glb",
  },
  {
    label: "Transparent render",
    file: "renders/gastric-rugae-maw.png",
  },
  {
    label: "Readable preview render",
    file: "renders/gastric-rugae-maw-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/pancreatic-membrane-slab.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/pancreatic-membrane-slab.glb",
  },
  {
    label: "Transparent render",
    file: "renders/pancreatic-membrane-slab.png",
  },
  {
    label: "Readable preview render",
    file: "renders/pancreatic-membrane-slab-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/adhesive-spleen-fold.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/adhesive-spleen-fold.glb",
  },
  {
    label: "Transparent render",
    file: "renders/adhesive-spleen-fold.png",
  },
  {
    label: "Readable preview render",
    file: "renders/adhesive-spleen-fold-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/inverted-membrane-cavity.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/inverted-membrane-cavity.glb",
  },
  {
    label: "Transparent render",
    file: "renders/inverted-membrane-cavity.png",
  },
  {
    label: "Readable preview render",
    file: "renders/inverted-membrane-cavity-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/valve-cusp-maw.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/valve-cusp-maw.glb",
  },
  {
    label: "Transparent render",
    file: "renders/valve-cusp-maw.png",
  },
  {
    label: "Readable preview render",
    file: "renders/valve-cusp-maw-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/pleural-fissure-bloom.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/pleural-fissure-bloom.glb",
  },
  {
    label: "Transparent render",
    file: "renders/pleural-fissure-bloom.png",
  },
  {
    label: "Readable preview render",
    file: "renders/pleural-fissure-bloom-preview.png",
  },
  {
    label: "STL print export",
    file: "exports/stl/pyloric-fold-gate.stl",
  },
  {
    label: "GLB web/object export",
    file: "exports/glb/pyloric-fold-gate.glb",
  },
  {
    label: "Transparent render",
    file: "renders/pyloric-fold-gate.png",
  },
  {
    label: "Readable preview render",
    file: "renders/pyloric-fold-gate-preview.png",
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
