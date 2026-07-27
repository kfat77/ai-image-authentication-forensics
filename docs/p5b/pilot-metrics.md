# P5-B Pilot Metrics

Metrics are operational observations by frozen pilot batch and scenario, not public accuracy claims. Every metric reports its numerator, denominator, exclusions, uncertainty, and data/analysis-version references.

| Metric | Definition | Required breakdown / interpretation |
|---|---|---|
| Uncertain rate | reports whose system assessment is `uncertain` divided by completed analyses | scenario, transformation, Provider/Registry configuration; uncertainty is allowed, not an error by itself |
| Human review rate | completed analyses receiving authorised feedback divided by completed analyses | scenario and reviewer availability; excludes withdrawn samples with stated denominator |
| Evidence completeness rate | reports meeting the declared evidence-manifest/provenance/version completeness checks divided by completed reports | evidence category and missing-data reason; no metadata is not negative origin evidence |
| Report generation success rate | successfully hash-bound JSON/PDF reports divided by admitted analysis attempts | input error, storage error, processing error, and retry policy separately |
| System stability | availability, analysis completion, error/retry, storage/database health, and audit-verification observations during the pilot window | no image bytes in telemetry; report the collection method and observation window |
| Audit integrity | audit events and chains verified divided by expected pilot events/chains | broken, missing, and unverified records remain visible and block closeout |
| Review agreement | compatible feedback outcomes divided by comparable feedback pairs | report `UNDETERMINED` separately; agreement is procedure consistency, not origin truth |

False-alert and missed-alert observations may be calculated only against the pilot's documented curated/reference labels and declared scope. They must remain in the failure register and must not be advertised as general detection accuracy.

## Minimum pilot dashboard fields

`pilot_batch_id`, time window, admitted/withdrawn/excluded counts, analysis version, Registry references, scenario coverage, every metric above, failure counts by category, and unresolved risks.
