# Registry signing specification

The record hash is SHA-256 over canonical `{record_type,payload}` JSON. The signature covers that hash. Any payload change causes hash and signature verification to fail. P4-C uses injected test signing keys; institutional keys and signer approval are deferred.
