"""Phase Diagrid: a geometric, graded lattice lantern with no figurative motif."""

import math
import runpy
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
geometry = runpy.run_path(str(HERE / "generate.py"), run_name="lantern_mesh_library")
TAU = 2 * math.pi
HEIGHT = 180


def radius(theta, z):
    u = z / HEIGHT
    # Eight flat facets turn through 31 degrees from the base to the mouth.
    phase = .54 * u + .055 * math.sin(TAU * u)
    facet = (theta - phase + math.pi / 8) % (math.pi / 4) - math.pi / 8
    apothem = 58 + 11 * math.sin(math.pi * u) - 7 * u
    return apothem / math.cos(facet)


def line_distance(value):
    return abs(value - round(value))


def solid(theta, z):
    if z < 14 or z > HEIGHT - 14:
        return True
    u = theta / TAU
    t = z / HEIGHT
    # Two crossing families of diagonal bands. The nonlinear phase shifts
    # crossings up and down, gradually changing cell height and orientation.
    phase = .16 * math.sin(TAU * t) + .10 * t * t
    a = 7 * u + 3.4 * t + phase + .055 * math.sin(3 * theta + 1.7 * t)
    b = 7 * u - 4.35 * t + phase - .045 * math.sin(2 * theta - 2.2 * t)
    width_a = .084 + .012 * math.sin(2.7 * math.pi * t)
    width_b = .082 + .010 * math.cos(2.3 * math.pi * t)
    return line_distance(a) < width_a or line_distance(b) < width_b


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    porcelain = geometry["material"]("matte_mineral_white", (.78, .80, .76), roughness=.72)
    inner = geometry["material"]("warm_white_section", (.61, .63, .58), roughness=.78)
    shade = geometry["build_shade"]("phase-diagrid", HEIGHT, radius, solid, porcelain, inner)
    scene = geometry["setup_scene"]("phase-diagrid", HEIGHT, (240, -280, 205), 285)
    scene.view_settings.exposure = 2.05
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (.016, .017, .018, 1)
    bpy.ops.object.light_add(type="AREA", location=(145, -225, 185))
    fill = bpy.context.object
    fill.name = "neutral_front_fill"
    fill.data.energy = 25000
    fill.data.color = (1, .98, .91)
    fill.data.size = 155
    geometry["add_led"]((0, 0, 84))
    geometry["export_and_render"]("phase-diagrid", shade, scene)


if __name__ == "__main__":
    main()
