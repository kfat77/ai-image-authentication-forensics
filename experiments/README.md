# Experiments

Experiments are offline, versioned research records. They may only consume an approved dataset manifest. P2-A provides `run_p2a_smoke.py`, which uses a deterministic **synthetic feature fixture**, not images, to validate feature → baseline → calibration → metrics → checkpoint-record plumbing.

Run it with:

```powershell
$env:PYTHONPATH = 'backend'
python experiments/run_p2a_smoke.py
```

The resulting record is explicitly not evidence of AI-image detection, model attribution or production readiness.
