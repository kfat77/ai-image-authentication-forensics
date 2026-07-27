# Provider admission

A signed `ProviderAdmissionRecord` is created only after Registry verification. It binds:

```json
{
  "provider_id": "...",
  "provider_version": "...",
  "model_record_hash": "...",
  "calibration_record_hash": "...",
  "scope_hash": "...",
  "approval_record_hash": "..."
}
```

Admission requires the Provider identity to be registered, both model and calibration records to be signed and APPROVED, calibration `model_id` to equal the model's `model_id`, model `calibration_id` to equal the calibration ID, provider ID to equal the model's provider ID, and the declared scope hash to equal the approved calibration scope. `approval_record_hash` commits to the terminal model and calibration approval-event hashes. Any mismatch rejects admission.

For formal ML evidence, the Authentication Engine performs this lookup at report time. Callers cannot supply model or calibration hashes. The report stores only Registry-derived references and each provider evidence item carries `registry_verified` and `verified_record_hash`. These references support reproduction; they never alter an authenticity status directly.
