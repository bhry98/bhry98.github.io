---
# COPY THIS FILE to start a new How-To guide. This template is excluded from the site (see
# `exclude_docs` in mkdocs.yml).
#
# 1. Copy it to docs/how-to/<topic>/<guide-name>.md   e.g. docs/how-to/openshift/deploy-app.md
# 2. Put screenshots in docs/how-to/<topic>/images/    e.g. 01-login.png, 02-create-project.png
# 3. Add the guide to the `How-To` section of `nav:` in mkdocs.yml
# 4. Add a card for it in docs/how-to/index.md
title: How to <do something>
description: One sentence for search engines and link previews.
tags:
  - <Technology>
---

# How to <do something>

One or two sentences: what this tool is and why you'd do this.

By the end of this guide you will have:

- [x] Result 1
- [x] Result 2

## Prerequisites

| Requirement | Version |
|---|---|
| Tool | x.y |

## Step 1: <First action>

```bash
command --to-run
```

Screenshot with a caption (click to zoom is automatic):

![Describe what the screenshot shows (alt text)](images/01-example.png)
/// caption
Short caption under the image.
///

Smaller image, or one that should not open in the zoom viewer:

![Alt text](images/02-example.png){ width="420" }
![Alt text](images/03-example.png){ .off-glb }

## Step 2: <Next action>

!!! tip
    Helpful hint.

!!! warning
    Something that can go wrong.

=== "Option A"

    Steps for option A.

=== "Option B"

    Steps for option B.

## Verify it works

```bash
command --to-check
```

:material-check-circle:{ .bh-ok } **Done.** What the reader has now.

## Troubleshooting

??? question "Common error message"
    How to fix it.

## Next steps

- [Related guide](../index.md)
