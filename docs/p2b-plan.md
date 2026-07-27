# P2-B entry plan

P2-B may begin only after explicit confirmation and the following gates are complete:

1. Approve at least one real-image and one generated-image dataset version through the registry, including licence, privacy, and permitted-use review.
2. Create hashed, leakage-audited train/calibration/test manifests with generator and transformation coverage.
3. Select a small, licensed encoder candidate through the uniform interface; record checkpoint provenance and model card before any download or use.
4. Run Task A and Task C on real approved image data, then report all required slices, calibration, uncertainty, and error cases.
5. Add Task B only when labels include documented known generators and a deliberately held-out unknown set.
6. Perform independent reproducibility and governance review before discussing any deployment experiment.

P2-B remains research work. It must not expose a production detection API, make a product-origin claim, or use unreviewed data.
