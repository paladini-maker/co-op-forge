#!/usr/bin/env python3
"""Validate the single-page app and its checked-in Blender bridge."""
from __future__ import annotations

import html.parser
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = ROOT / "index.html"
BRIDGE = ROOT / "tools" / "co_op_forge_blender_bridge.py"
REQUIRED_PATHS = (
    ROOT / "README.md",
    ROOT / "LICENSE",
    ROOT / ".github" / "workflows" / "validate.yml",
    ROOT / ".github" / "workflows" / "pages.yml",
    ROOT / "docs" / "GITHUB_INTEGRATION.md",
    ROOT / "docs" / "FORMAT_SUPPORT.md",
    ROOT / "docs" / "GOLDSRC_PIPELINE.md",
    ROOT / "tests" / "test_project.py",
    BRIDGE,
)


class ScriptCollector(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.current_attrs: dict[str, str | None] | None = None
        self.current: list[str] = []
        self.scripts: list[tuple[dict[str, str | None], str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "script":
            self.current_attrs = dict(attrs)
            self.current = []

    def handle_data(self, data: str) -> None:
        if self.current_attrs is not None:
            self.current.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self.current_attrs is not None:
            self.scripts.append((self.current_attrs, "".join(self.current)))
            self.current_attrs = None
            self.current = []


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> int:
    for path in REQUIRED_PATHS:
        if not path.is_file():
            fail(f"required project file missing: {path.relative_to(ROOT)}")

    html = APP.read_text(encoding="utf-8")
    parser = ScriptCollector()
    parser.feed(html)
    parser.close()
    if parser.current_attrs is not None:
        fail("unterminated script tag in index.html")

    plain_scripts = [body for attrs, body in parser.scripts if attrs.get("id") == "blenderBridgeSource"]
    if len(plain_scripts) != 1:
        fail("expected exactly one script#blenderBridgeSource block")
    embedded_bridge = plain_scripts[0].strip()
    external_bridge = BRIDGE.read_text(encoding="utf-8").strip()
    if embedded_bridge != external_bridge:
        fail("tools/co_op_forge_blender_bridge.py is out of sync with the embedded bridge")

    required_tokens = (
        'id="modelFile"',
        'id="meshCanvas"',
        'id="pipelineStatus"',
        "function parseGLB(",
        "function buildRiggedSMD(",
        "function downloadBridge(",
        "goldsrc_compatibility_report",
    )
    for token in required_tokens:
        if token not in html:
            fail(f"application feature marker not found: {token}")

    try:
        compile(external_bridge, str(BRIDGE), "exec")
    except SyntaxError as exc:
        fail(f"Blender bridge has Python syntax error: {exc}")

    node = shutil.which("node")
    runtime_scripts = [
        body for attrs, body in parser.scripts
        if attrs.get("id") != "blenderBridgeSource"
        and attrs.get("type", "").lower() not in {"text/plain", "application/json"}
    ]
    if node is None:
        print("WARN: Node.js unavailable; JavaScript syntax check skipped.")
    else:
        for index, body in enumerate(runtime_scripts, 1):
            with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
                handle.write(body)
                temp_path = pathlib.Path(handle.name)
            try:
                result = subprocess.run([node, "--check", str(temp_path)], capture_output=True, text=True, check=False)
                if result.returncode:
                    fail(f"inline JavaScript block {index} failed syntax check:\n{result.stderr or result.stdout}")
            finally:
                temp_path.unlink(missing_ok=True)

    print(f"PASS: found {len(parser.scripts)} script blocks")
    print("PASS: embedded Blender bridge matches tools/co_op_forge_blender_bridge.py")
    print("PASS: Blender bridge Python syntax")
    if node:
        print(f"PASS: {len(runtime_scripts)} runtime JavaScript block(s) pass node --check")
    print("PASS: required app, docs, and workflow files exist")
    return 0


if __name__ == "__main__":
    sys.exit(main())
