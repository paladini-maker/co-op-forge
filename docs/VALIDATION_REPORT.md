# Validation report

This report reflects static checks run while preparing the GitHub repository bundle.

## Checks run in this packaging pass

- `python scripts/validate_project.py` — passed.
- `python -m unittest discover -s tests -v` — passed (5 tests).
- Inline application JavaScript checked with Node.js `--check` — passed.
- Blender bridge Python syntax checked with Python `compile()` without importing Blender runtime modules — passed.
- Confirmed `tools/co_op_forge_blender_bridge.py` matches the bridge embedded in `index.html` exactly after trimming the final newline — passed.
- Required app, documentation and GitHub workflow files exist — passed.

## Not certified by these checks

- Executing the bridge inside a live Blender session.
- Full interactive browser regression tests for every OBJ/SMD/GLB model variant.
- Compiling generated SMD/QC into a GoldSrc/Sven Co-op MDL.
- Testing compiled models in a model viewer or in the game.
- Exact preservation of source rig, weights, animation sequences, materials, textures, hitboxes, or every GLB extension.

These checks validate project structure and source syntax; they do not certify universal asset compatibility.
