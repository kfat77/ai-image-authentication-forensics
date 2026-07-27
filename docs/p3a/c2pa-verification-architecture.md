# C2PA Verification Architecture

P1 currently reads embedded markers only. P3 introduces this future verifier pipeline:

`manifest discovery -> manifest parse -> signature verification -> certificate validation -> trust-policy evaluation -> VALID|INVALID|NOT_PRESENT|UNKNOWN`.

`NOT_PRESENT` never infers AI generation. `VALID` means only that a statement and signer passed the configured verifier/trust policy; it is not an image-truth guarantee. The verifier, trust anchors, revocation policy, timestamps and errors must be stored as evidence provenance.
