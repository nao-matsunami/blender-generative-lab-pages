import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const jobsDir = path.join(rootDir, "blender-jobs");
const target = process.argv[2] || "all";

const studies = {
  organic: "offline/generate_organic_growth_vessel.py",
  voronoi: "offline/generate_voronoi_light_shell.py",
  seed: "offline/generate_luminous_seed_vessel.py",
  coral: "offline/generate_tidal_coral_helix.py",
  bloom: "offline/generate_manta_bloom_shell.py",
  spore: "offline/generate_spore_current_lantern.py",
  kelp: "offline/generate_kelp_pulse_torus.py",
  viscera: "offline/generate_visceral_tide_knot.py",
  neural: "offline/generate_neural_gut_bloom.py",
  maw: "offline/generate_membrane_maw_cluster.py",
  arterial: "offline/generate_arterial_fold_nest.py",
  coilwomb: "offline/generate_peristaltic_coil_womb.py",
  adhesion: "offline/generate_adhesion_gut_wreath.py",
  hepatic: "offline/generate_hepatic_vessel_bloom.py",
  valvular: "offline/generate_valvular_chamber_bloom.py",
  alveolar: "offline/generate_alveolar_sac_cluster.py",
  renal: "offline/generate_renal_pelvis_vessel.py",
  gastric: "offline/generate_gastric_rugae_maw.py",
  pancreatic: "offline/generate_pancreatic_membrane_slab.py",
  spleen: "offline/generate_adhesive_spleen_fold.py",
  cavity: "offline/generate_inverted_membrane_cavity.py",
  valvecusp: "offline/generate_valve_cusp_maw.py",
};

const selected = target === "all" ? Object.keys(studies) : [target];

for (const key of selected) {
  if (!studies[key]) {
    console.error(`Unknown job: ${key}`);
    console.error(`Use one of: ${Object.keys(studies).join(", ")}, all`);
    process.exit(1);
  }
}

await fs.mkdir(jobsDir, { recursive: true });

const stamp = new Date().toISOString().replaceAll(":", "").replaceAll(".", "");
const jobName = `${stamp}_${target}.job.py`;
const jobPath = path.join(jobsDir, jobName);

const scriptLines = [
  "import os",
  "import runpy",
  "from pathlib import Path",
  "",
  `PROJECT_ROOT = Path(${JSON.stringify(rootDir)})`,
  "os.environ['BLENDER_LAB_ROOT'] = str(PROJECT_ROOT)",
  "",
  ...selected.flatMap((key) => [
    `print(${JSON.stringify(`Running ${key}`)})`,
    `runpy.run_path(str(PROJECT_ROOT / ${JSON.stringify(studies[key])}), run_name='__main__')`,
    "",
  ]),
  `print(${JSON.stringify(`Completed ${target}`)})`,
  "",
];

await fs.writeFile(jobPath, scriptLines.join("\n"), "utf8");
console.log(`Submitted ${jobPath}`);
console.log("Keep Blender open with offline/gui_job_watcher.py running.");
