# Research data workspace

This directory deliberately contains no external image assets in P2-B1. A dataset may be materialised here only after its matching manifest is approved, its legal/privacy review is recorded, and a hash-verified data index has passed split validation.

Expected layout after approval:

```text
datasets/<dataset-name>/<version>/
  index.jsonl
  images/...
```

No loader in this repository provides a random split operation.
