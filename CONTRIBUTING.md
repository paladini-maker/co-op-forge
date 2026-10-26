# Contributing

Thanks for helping improve Co-Op Forge.

## Before opening a pull request

- Keep the main application self-contained in `index.html` unless a dependency is justified and documented.
- Document parser or exporter limitations accurately; never describe preflight as proof that an MDL compiles.
- Add or update a regression fixture for parser/exporter changes.
- Run `python scripts/validate_project.py` and `python -m unittest discover -s tests -v`.
- Do not commit copyrighted game models, commercial assets, or user-provided reference images without permission.
- Keep Blender bridge source synchronized with the copy embedded in `index.html`; the validator checks this.

## Pull requests

Explain the tested formats and tools, include a minimal reproducible input when legally distributable, and state known compatibility losses.
