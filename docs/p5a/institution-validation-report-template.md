# Institution Validation Report Template

> **Controlled validation record — not a judicial opinion, certification, public claim, or proof that any image is AI-generated.**

## 1. Identification

- Validation Program / batch ID:
- Validation date range:
- Institution environment identifier (non-public):
- Report version and hash:
- Authors, reviewers, and approval roles:

## 2. System and governance configuration

| Item | Required value |
|---|---|
| System / code version | commit or immutable build ID |
| Evidence-engine version | version and configuration hash |
| Authentication/Fusion version | version and rules reference |
| Model Record(s) | approved record hash, or `not used` |
| Calibration Record(s) | approved record hash, or `not used` |
| Provider Admission Record(s) | approved record hash, or `not used` |
| Key-provider mode | test/institution supplied; no secret material |

## 3. Data scope and governance

- Scenario matrix version:
- Number admitted / rejected / excluded:
- Per-scenario coverage and known gaps:
- Licence and source review procedure:
- Dataset/sample manifest hash:
- Prohibited or unrepresented conditions:

## 4. Results

Report aggregate and per-scenario values, including denominator and confidence interval method where defined by the institution:

| Metric | Overall | By scenario | Interpretation / limitation |
|---|---:|---|---|
| False Positive Rate |  |  | conditioned on curated labels and scope |
| False Negative Rate |  |  | conditioned on curated labels and scope |
| Uncertain Rate |  |  | uncertainty is a permitted outcome |
| Evidence Completeness |  |  | reports available evidence, not truth |
| Report Reproducibility |  |  | hash/version/manifest chain verification |
| Review Agreement |  |  | independent-review protocol and abstentions |

## 5. Failure, exclusion, and disagreement register

Include every false positive, false negative, `uncertain`, processing failure, out-of-scope exclusion, and reviewer disagreement. Do not remove or aggregate away adverse examples.

| Sample hash / ID | Scenario | Outcome | Review decision | Root-cause hypothesis | Required follow-up |
|---|---|---|---|---|---|

## 6. Limitations and recommended usage scope

- Explicitly supported population and transformations:
- Excluded conditions and coverage gaps:
- Model and calibration limitations:
- Evidence/provenance limitations:
- Recommended internal use: human-reviewed, bounded, non-judicial assessment only.
- Not authorized: public service, automated adverse decision, judicial conclusion, or 100% detection claim.

## 7. Conclusion and next decision

Choose one: `continue controlled validation`, `narrow scope and repeat`, or `halt pending remediation`.

This decision cannot itself authorize P5-B or production deployment; it identifies the evidence needed for a separate institutional pilot approval.
