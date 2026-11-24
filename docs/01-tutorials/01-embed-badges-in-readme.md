# Tutorial: Embed Badges in a Project README

> **Learning Goal:** Clone `open-source-badges`, inspect local SVG and PNG dimensions with Python, and embed working badges with CC-BY 4.0 attribution in a Markdown file.
>
> **Environment Warning:** Run validation commands inside a temporary test directory or local clone before updating public project READMEs.

## Prerequisites

Make sure your environment has:

- `git` and Python 3.8+
- Standard terminal (`bash` or `PowerShell`)

## Step 1: Clone the Repository and Inspect Assets

Clone this repository locally and inspect the tracked SVG and PNG files:

```bash
git clone https://github.com/jmrenouard/open-source-badges.git
cd open-source-badges
python -c "import pathlib; print(len(list(pathlib.Path('badges').rglob('*.svg'))), len(list(pathlib.Path('badges').rglob('*.png'))))"
```

Expected output:

```text
5 22
```

There are 5 vector `.svg` badges and 22 raster `.png` files under `badges/`.

## Step 2: Add an Open Source Love SVG and MIT License Badge

Create a sample Markdown file (`sample_README.md`) referencing the vector Open Source v1 badge (`120x20`) and MIT license badge (`100x20`):

```markdown
# My Sample Project

[![Open Source Love](https://raw.githubusercontent.com/jmrenouard/open-source-badges/master/badges/open-source-v1/open-source.svg)](https://github.com/jmrenouard/open-source-badges)
[![MIT License](https://raw.githubusercontent.com/jmrenouard/open-source-badges/master/badges/licence-mit/mit.svg)](https://opensource.org/licenses/MIT)
```

For in-repository documentation inside a clone of `open-source-badges`, use relative paths such as `badges/open-source-v1/open-source.svg`.

## Step 3: Verify Badge Assets Locally

Run the repository verification suite to confirm every SVG XML file and PNG header parses cleanly:

```bash
python -B -m unittest discover -s tests -v
```

Expected output:

```text
Ran 7 tests in 0.1s

OK
```

## Next Steps

- Strict embedding procedure: [Embed and Verify Badges](../02-how-to-guides/embed-and-verify-badges.md)
- Exact SVG/PNG dimension table: [Badge Catalog and Dimensions](../03-reference/badge-catalog-and-dimensions.md)
- Format and hosting trade-offs: [SVG vs. PNG and Hosting Design](../04-explanation/svg-vs-png-and-hosting-design.md)
