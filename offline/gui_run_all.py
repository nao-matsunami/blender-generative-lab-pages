"""Run all Blender Generative Lab studies from Blender's GUI.

Use this when command-line/background Blender crashes but the normal Blender UI
opens. In Blender:

1. Open the Scripting workspace.
2. Text > Open this file.
3. Press Run Script.
"""

import os
import runpy
from pathlib import Path


PROJECT_ROOT = Path("/Users/nao/Documents/Codex/2026-08-03-xr-glsl-vj/blender-generative-lab")
os.environ["BLENDER_LAB_ROOT"] = str(PROJECT_ROOT)

scripts = [
    PROJECT_ROOT / "offline" / "generate_organic_growth_vessel.py",
    PROJECT_ROOT / "offline" / "generate_voronoi_light_shell.py",
    PROJECT_ROOT / "offline" / "generate_luminous_seed_vessel.py",
    PROJECT_ROOT / "offline" / "generate_tidal_coral_helix.py",
    PROJECT_ROOT / "offline" / "generate_manta_bloom_shell.py",
    PROJECT_ROOT / "offline" / "generate_spore_current_lantern.py",
    PROJECT_ROOT / "offline" / "generate_kelp_pulse_torus.py",
    PROJECT_ROOT / "offline" / "generate_visceral_tide_knot.py",
    PROJECT_ROOT / "offline" / "generate_neural_gut_bloom.py",
    PROJECT_ROOT / "offline" / "generate_membrane_maw_cluster.py",
    PROJECT_ROOT / "offline" / "generate_arterial_fold_nest.py",
    PROJECT_ROOT / "offline" / "generate_peristaltic_coil_womb.py",
    PROJECT_ROOT / "offline" / "generate_adhesion_gut_wreath.py",
    PROJECT_ROOT / "offline" / "generate_hepatic_vessel_bloom.py",
    PROJECT_ROOT / "offline" / "generate_valvular_chamber_bloom.py",
    PROJECT_ROOT / "offline" / "generate_alveolar_sac_cluster.py",
    PROJECT_ROOT / "offline" / "generate_renal_pelvis_vessel.py",
    PROJECT_ROOT / "offline" / "generate_gastric_rugae_maw.py",
]

for script in scripts:
    print(f"Running {script}")
    runpy.run_path(str(script), run_name="__main__")

print("Blender Generative Lab GUI run complete.")
