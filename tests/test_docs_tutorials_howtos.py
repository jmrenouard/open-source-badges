"""Automated SVG/PNG asset integrity, README parity, and Diataxis verification suite."""

from __future__ import annotations

import pathlib
import re
import struct
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BADGES_DIR = REPO_ROOT / "badges"
DOCS_DIR = REPO_ROOT / "docs"

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SIZE_IN_NAME_RE = re.compile(r"-(\d+)x(\d+)\.png$")
RAW_BADGE_URL_RE = re.compile(
    r"https://raw\.githubusercontent\.com/jmrenouard/open-source-badges/master/(badges/[^\s)\]`\"']+)"
)
LOCAL_BADGE_LINK_RE = re.compile(r"\((badges/[^\s)]+)\)")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
FENCE_RE = re.compile(r"^([ \t]*)(`{3,}|~{3,})(.*)$")
BOX_OR_ARROW_RE = re.compile(r"(?:[┌┐└┘╔╗╚╝├┤┬┴┼═─]{2,}|\+[-=]{2,}\+|(?<![<!])-->|<--)")
INDENTED_MERMAID_RE = re.compile(r"^[ \t]+(?:```|~~~)mermaid\b", re.MULTILINE)
UNFENCED_MERMAID_HEADER_RE = re.compile(r"^(?:flowchart|graph\s+(?:TD|TB|LR)|sequenceDiagram)\b")

WEAK_MODALS_RE = re.compile(r"\b(?:should|would|may|might|shall|ought)\b", re.IGNORECASE)
CONTRACTIONS_RE = re.compile(
    r"\b(?:don't|doesn't|didn't|won't|can't|isn't|aren't|wasn't|weren't|"
    r"haven't|hasn't|hadn't|you're|we're|they're|it's|that's)\b",
    re.IGNORECASE,
)
FRENCH_STOPWORD_RE = re.compile(
    r"[àâäçéèêëîïôöùûüÿœæ]|"
    r"\b(?:procédure|tutoriel|prérequis|étape|vérification|déploiement|référence)\b",
    re.IGNORECASE,
)


def _strip_code_blocks(text: str) -> str:
    """Return markdown prose with fenced code blocks removed."""
    kept: list[str] = []
    in_fence = False
    fence_char = ""
    fence_len = 0
    for line in text.splitlines():
        match = FENCE_RE.match(line)
        if not in_fence and match:
            in_fence = True
            fence_char = match.group(2)[0]
            fence_len = len(match.group(2))
            continue
        if in_fence:
            stripped = line.strip()
            if stripped and set(stripped) == {fence_char} and len(stripped) >= fence_len:
                in_fence = False
            continue
        kept.append(line)
    return "\n".join(kept)


class TestDocsTutorialsHowtos(unittest.TestCase):
    """Validate badge assets, README/reference parity, Diataxis, STE, and Mermaid checks."""

    def test_svg_xml_well_formed_and_dimensions(self) -> None:
        svgs = sorted(BADGES_DIR.rglob("*.svg"))
        self.assertEqual(len(svgs), 5)
        for svg_path in svgs:
            with self.subTest(svg=svg_path.relative_to(REPO_ROOT).as_posix()):
                root = ET.parse(svg_path).getroot()
                self.assertTrue(root.tag.endswith("svg"))
                width = int(root.attrib["width"])
                height = int(root.attrib["height"])
                self.assertGreater(width, 0)
                self.assertGreater(height, 0)

    def test_png_headers_and_dimensions_match_filenames(self) -> None:
        pngs = sorted(BADGES_DIR.rglob("*.png"))
        self.assertEqual(len(pngs), 22)
        for png_path in pngs:
            with self.subTest(png=png_path.relative_to(REPO_ROOT).as_posix()):
                data = png_path.read_bytes()
                self.assertTrue(data.startswith(PNG_SIGNATURE), "Invalid PNG header")
                self.assertGreaterEqual(len(data), 24)
                self.assertEqual(data[12:16], b"IHDR")
                width, height = struct.unpack(">II", data[16:24])
                self.assertGreater(width, 0)
                self.assertGreater(height, 0)
                name_dims = SIZE_IN_NAME_RE.search(png_path.name)
                if name_dims:
                    self.assertEqual((width, height), (int(name_dims.group(1)), int(name_dims.group(2))))

    def test_readme_and_reference_cover_all_badges_without_stale_urls(self) -> None:
        readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        ref_text = (DOCS_DIR / "03-reference/badge-catalog-and-dimensions.md").read_text(encoding="utf-8")

        for legacy_host in (
            "frapsoft.com",
            "badges.gitter.im",
            "plus.google.com",
            "github.com/ellerbrock/open-source-badge/",
            "http://creativecommons.org/",
            "150x22px",
        ):
            self.assertNotIn(legacy_host, readme_text, f"Legacy pattern '{legacy_host}' left in README.md")

        # Ensure SVG and PNG sizes match verified assets in README.md.
        self.assertIn("### SVG (`100x20px`)", readme_text)
        self.assertIn("### PNG (`90x20px`", readme_text)
        self.assertIn("Size `150x25px`:", readme_text)

        all_assets = sorted(
            [p.relative_to(REPO_ROOT).as_posix() for p in BADGES_DIR.rglob("*.svg")]
            + [p.relative_to(REPO_ROOT).as_posix() for p in BADGES_DIR.rglob("*.png")]
        )
        self.assertEqual(len(all_assets), 27)
        for rel_asset in all_assets:
            self.assertIn(rel_asset, readme_text, f"{rel_asset} missing in README.md")
            self.assertIn(rel_asset, ref_text, f"{rel_asset} missing in Reference catalog")

        for doc_file in [REPO_ROOT / "README.md", *sorted(DOCS_DIR.rglob("*.md"))]:
            text = doc_file.read_text(encoding="utf-8")
            for rel_raw in RAW_BADGE_URL_RE.findall(text):
                self.assertTrue((REPO_ROOT / rel_raw).is_file(), f"Missing raw URL target {rel_raw} in {doc_file}")
            for rel_local in LOCAL_BADGE_LINK_RE.findall(text):
                self.assertTrue(
                    (REPO_ROOT / rel_local).is_file(), f"Missing local target {rel_local} in {doc_file}"
                )

    def test_diataxis_structure_links_and_ste_rules(self) -> None:
        for rel in (
            "index.md",
            "01-tutorials/index.md",
            "01-tutorials/01-embed-badges-in-readme.md",
            "02-how-to-guides/index.md",
            "02-how-to-guides/embed-and-verify-badges.md",
            "03-reference/index.md",
            "03-reference/badge-catalog-and-dimensions.md",
            "04-explanation/index.md",
            "04-explanation/svg-vs-png-and-hosting-design.md",
        ):
            self.assertTrue((DOCS_DIR / rel).is_file(), f"Missing docs/{rel}")

        for page in [REPO_ROOT / "README.md", *sorted(DOCS_DIR.rglob("*.md"))]:
            prose = _strip_code_blocks(page.read_text(encoding="utf-8"))
            for target in LINK_RE.findall(prose):
                clean = target.split("#", 1)[0].strip()
                if not clean or clean.startswith(("http://", "https://", "mailto:")):
                    continue
                resolved = (page.parent / clean).resolve()
                self.assertTrue(
                    resolved.exists(),
                    f"Broken relative link '{target}' in {page.relative_to(REPO_ROOT)}",
                )

        for guide in sorted((DOCS_DIR / "02-how-to-guides").glob("*.md")):
            if guide.name == "index.md":
                continue
            prose = _strip_code_blocks(guide.read_text(encoding="utf-8"))
            self.assertIsNone(WEAK_MODALS_RE.search(prose), f"Weak modal in {guide}")
            self.assertIsNone(CONTRACTIONS_RE.search(prose), f"Contraction in {guide}")
            self.assertNotIn(";", prose, f"Semicolon in {guide}")
            self.assertFalse(re.search(r"^##\s+(?:Why|Architecture|Context)\b", prose, re.M))

    def test_tutorial_python_command_count_and_sample_syntax(self) -> None:
        tut = (DOCS_DIR / "01-tutorials/01-embed-badges-in-readme.md").read_text(encoding="utf-8")
        self.assertIn("5 22", tut)
        self.assertIn("Ran 7 tests", tut)
        self.assertIn("README.md", tut)

    def test_optional_skill_validators_if_installed(self) -> None:
        skills_root = pathlib.Path.home() / ".gemini/config/skills"
        diataxis_script = skills_root / "diataxis-docs/scripts/diataxis_check.py"
        if diataxis_script.is_file():
            proc = subprocess.run(
                [sys.executable, str(diataxis_script), str(DOCS_DIR), "--strict", "--check-ste", "--lang", "en"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("0 error(s), 0 warning(s)", proc.stdout)

        ste_script = skills_root / "simplified-technical-english/scripts/ste_check.py"
        if ste_script.is_file():
            guides = sorted(
                str(p)
                for p in (DOCS_DIR / "02-how-to-guides").glob("*.md")
                if p.name != "index.md"
            )
            proc = subprocess.run(
                [sys.executable, str(ste_script), "--mode", "procedural", *guides],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("Result: 0 errors, 0 warnings.", proc.stdout)

    def test_diagrams_mermaid_no_ascii_and_english_only(self) -> None:
        md_files = sorted(
            p for p in REPO_ROOT.rglob("*.md") if ".git" not in p.parts and ".pytest_cache" not in p.parts
        )
        mermaid_count = 0
        for md_path in md_files:
            raw = md_path.read_text(encoding="utf-8")
            self.assertIsNone(INDENTED_MERMAID_RE.search(raw), f"Indented mermaid in {md_path}")
            in_fence = False
            fence_char = ""
            fence_len = 0
            fence_info = ""
            for idx, line in enumerate(raw.splitlines(), start=1):
                match = FENCE_RE.match(line)
                if not in_fence and match:
                    in_fence = True
                    fence_char = match.group(2)[0]
                    fence_len = len(match.group(2))
                    fence_info = match.group(3).strip().lower()
                    if fence_info == "mermaid":
                        mermaid_count += 1
                    continue
                if in_fence:
                    stripped = line.strip()
                    if stripped and set(stripped) == {fence_char} and len(stripped) >= fence_len:
                        in_fence = False
                        fence_info = ""
                        continue
                    if fence_info != "mermaid":
                        self.assertIsNone(
                            UNFENCED_MERMAID_HEADER_RE.match(line.strip()),
                            f"Untagged mermaid syntax at {md_path}:{idx}",
                        )
                        self.assertIsNone(
                            BOX_OR_ARROW_RE.search(line),
                            f"ASCII/box diagram at {md_path}:{idx}: {line}",
                        )
                    continue

                if "-->" not in line and "<--" not in line:
                    self.assertIsNone(BOX_OR_ARROW_RE.search(line), f"ASCII line at {md_path}:{idx}")
            self.assertIsNone(FRENCH_STOPWORD_RE.search(_strip_code_blocks(raw)), f"French text in {md_path}")
        self.assertGreaterEqual(mermaid_count, 2)


if __name__ == "__main__":
    unittest.main()
