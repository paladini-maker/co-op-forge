# Co-Op Forge — Sven Co-op Player Rig Studio

A local-first browser prototype for inspecting OBJ/SMD/binary GLB geometry, positioning humanoid guide joints, and preparing a Blender → SMD/QC → GoldSrc workflow.

> This is not a universal or lossless converter. Generated weights are approximate, the source rig/animations are not automatically preserved, and the browser does not compile a playable MDL.

## Quick start

1. Open `index.html` in a modern browser. No frontend build or server is required.
2. Import a supported OBJ, SMD, or self-contained binary GLB 2.0 file.
3. Inspect the compatibility report, adjust rig markers, and export the project package.
4. If needed, use `tools/co_op_forge_blender_bridge.py` inside Blender to create an editable blockout armature from the exported JSON.
5. Verify geometry, weights, materials/textures, skeleton names, animation sequences, hitboxes and compiler limits in your GoldSrc toolchain.

## Development checks

Requires Python 3.10+ and Node.js 20+.

```bash
python scripts/validate_project.py
python -m unittest discover -s tests -v
```

GitHub Actions checks the project on pushes and pull requests. GitHub Pages deploys only `index.html` after `Settings → Pages → Source → GitHub Actions` is selected.

See [Format support](docs/FORMAT_SUPPORT.md), [GoldSrc workflow](docs/GOLDSRC_PIPELINE.md), and [GitHub integration](docs/GITHUB_INTEGRATION.md).

## License

MIT; see `LICENSE`.
