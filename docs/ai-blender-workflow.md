# AI + Blender Workflow

## Practical Use

Use AI as a design and scripting partner, not as an unchecked executor.

Good uses:

- propose form families
- generate Blender Python drafts
- make Geometry Nodes plans
- review mesh/export logic
- create variant parameters
- write product notes and pack descriptions

Risky uses:

- running unknown Python inside Blender
- downloading assets without checking license
- trusting printable status without slicer inspection
- assuming a generated mesh is manifold

## Prompt Pattern

```txt
Create a Blender Python generator for an organic vessel.
Constraints:
- millimeter scale
- minimum wall thickness 2.4 mm
- STL and GLB export
- transparent still render
- no external assets
- add comments only where needed
```

## Review Gate

Before running AI-generated Blender code:

- read file paths
- check delete operations
- check network/download operations
- check shell calls
- check output directories
- keep generated files inside this project

## Project Direction

The strongest direction is not only "AI makes a model." It is:

```txt
algorithm + Blender + AI critique
  -> printable object
  -> web preview
  -> render/video
  -> source/object pack
```

That keeps the work original and gives every study multiple outputs.
