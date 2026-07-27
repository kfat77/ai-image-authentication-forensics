# Validation Runs

Each P6-B Validation Run is append-only and records the exact Registry references (or their documented absence), frozen dataset manifest, code version, timestamp, data-admission result, metrics, and decision. A rejected preflight remains a Validation Run: it records why no candidate result was permitted and prevents later substitution of unverified artifacts.
