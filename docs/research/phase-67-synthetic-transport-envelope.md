# Nova Aegis Phase 67 - Synthetic Transport Envelope

## Experiment

Bind a local request to request ID, audience, task, method, and canonical parameter digest. A response must preserve request identity and include a response digest; cross-task responses fail closed.

## Decision

`ADAPT` as a metadata contract only. This does not implement HTTP, OAuth, PKCE, sessions, SSRF defenses, quotas, TLS, or network authority.
