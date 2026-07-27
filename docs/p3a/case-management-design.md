# Case Management Design

`CaseRecord` contains case ID, submitter, submission time, original file hash, frozen evidence bundle reference, analysis version, reviewer and final report hash.

Lifecycle: **submit -> freeze original and evidence -> analyse -> reviewer assessment -> report signature -> archive**. A case revision creates a new analysis/report reference; it never overwrites original evidence. Reviewer approval is a human accountability action, not an automatic authenticity conclusion.
