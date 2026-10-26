from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class ProjectStructureTests(unittest.TestCase):
    def test_github_pages_workflow_exists(self) -> None:
        workflow = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
        self.assertIn("actions/deploy-pages@v4", workflow)
        self.assertIn("branches: [main]", workflow)
        self.assertIn("index.html", workflow)

    def test_ci_workflow_runs_validator_and_tests(self) -> None:
        workflow = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
        self.assertIn("python scripts/validate_project.py", workflow)
        self.assertIn("python -m unittest discover -s tests -v", workflow)

    def test_application_has_glb_pipeline_and_privacy_notice(self) -> None:
        app = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("function parseGLB(", app)
        self.assertIn("function validateGLB(", app)
        self.assertIn("goldsrc_compatibility_report", app)
        self.assertIn("No data was uploaded", app)

    def test_external_bridge_is_embedded_in_app(self) -> None:
        app = (ROOT / "index.html").read_text(encoding="utf-8")
        bridge = (ROOT / "tools/co_op_forge_blender_bridge.py").read_text(encoding="utf-8").strip()
        marker = '<script type="text/plain" id="blenderBridgeSource">'
        self.assertIn(marker, app)
        embedded = app.split(marker, 1)[1].split("</script>", 1)[0].strip()
        self.assertEqual(embedded, bridge)

    def test_docs_do_not_promise_full_compatibility(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("no certifica", readme.lower())
        self.assertIn("LICENSE", readme)


if __name__ == "__main__":
    unittest.main()
