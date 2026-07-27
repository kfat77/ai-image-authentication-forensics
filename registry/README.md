# Dataset admission registry

`approved-manifests.json` is intentionally empty in P2-B1: the P2-A registry did not contain an externally approved dataset version. Candidate manifests are in `/manifests`; they cannot be used for experiments.

An approval entry must cite a manifest path and its canonical SHA-256, name the reviewer, approval date and scope, and declare training/commercial permission booleans. It may be added only after the source licence, permitted training use, commercial restrictions, and privacy review are resolved.
