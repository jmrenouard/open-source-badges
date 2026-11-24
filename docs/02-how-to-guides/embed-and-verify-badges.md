# Embed and Verify Badges

Refer to the [Badge Catalog](../03-reference/badge-catalog-and-dimensions.md) before you run this procedure.

## Preconditions

1. Make sure that Python 3 is installed on your workstation.
2. Make sure that all target badge files exist under `badges/`.
3. Make sure that you have write access to the target Markdown file.

## Safety Instructions

**CAUTION:** Do not link external deprecated hosts such as `badges.frapsoft.com` in new documents. Broken external links stop image displays in offline or restricted environments.

## Procedure

### Select and Insert a Badge

1. Open the [Badge Catalog](../03-reference/badge-catalog-and-dimensions.md) and select a badge path.

2. If the Markdown document is inside this repository, use the relative `badges/` path.

3. If the Markdown document is in an external repository, use the HTTPS raw GitHub URL on `master`.

4. Copy the Markdown snippet into the target file and set the license link URL.

5. Add CC-BY 4.0 attribution in the license section of your project documentation.

### Run Local Validation Checks

1. Open a terminal at the repository root.

2. Run the automated verification command:

```bash
python -B -m unittest discover -s tests -v
```

3. Make sure that all SVG XML checks and PNG checks pass without error.

## Verification Check

1. Examine the badge lines in the target Markdown file.

2. Confirm that every image path matches a tracked file in `badges/`.

3. Confirm that every stated size matches the dimensions in the [Badge Catalog](../03-reference/badge-catalog-and-dimensions.md).

## Rollback Procedure

If an error occurs in the Markdown file or test run, do this procedure:

1. Restore the previous file with Git:

```bash
git checkout -- README.md
```

2. Run `python -B -m unittest discover -s tests -v` again to confirm a clean state.

## Related Documentation

- Reference: [Badge Catalog and Dimensions](../03-reference/badge-catalog-and-dimensions.md)
- Explanation: [SVG vs. PNG and Asset Design](../04-explanation/svg-vs-png-and-hosting-design.md)
