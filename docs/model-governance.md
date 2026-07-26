# Model governance and use boundary

## What the service does

Version 0.2 uses deterministic, observable image features: dimensions, aspect ratio, average RGB colour and brightness. It maps these features to editable prompt templates for several image-generation ecosystems. The response identifies this method and version.

The candidate list is a set of workflow templates, **not** a classifier result. It intentionally exposes no numerical confidence because no calibrated model-source classifier or validation data exists in this release.

## What the service must not be used for

- Determining authorship, ownership, image provenance, a person's identity, intent, or truthfulness.
- Supporting eligibility, enforcement, surveillance, immigration, benefits, employment, education, criminal justice, or any other consequential decision about a person.
- Inferring a proprietary model's weights, training data, system prompt, or confidential settings.

## Human oversight

Every response includes `human_review.required: true`. A trained reviewer must evaluate output before it is published, used in a workflow, or relied on as evidence. The reviewer should record the input's authority, the intended creative use, the output selected, modifications made, and approval under the organisation's records policy.

## Change and evaluation gates

Before replacing the heuristic method or claiming a source-model classifier:

1. Define a lawful, documented, representative evaluation dataset and its licence/provenance.
2. Publish task-specific metrics, confidence calibration, error analysis and known failure modes.
3. Test for relevant quality and disparity risks; obtain independent review.
4. Version the model, prompts and evaluation report; approve the change through institutional change control.
5. Implement rollback, monitoring and an appeal/remediation route where output can affect people.
