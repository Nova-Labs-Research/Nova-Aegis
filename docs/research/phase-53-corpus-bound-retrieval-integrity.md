# Nova Aegis Phase 53 - Corpus-Bound Retrieval Integrity

## Scope

Phase 53 closes a replay gap found after Phase 52: a source could retain the same identifier while its content changed. Structural trace comparison alone does not prove that the replay corpus is the recorded corpus.

## Change

Retrieval traces now carry:

- a canonical SHA-256 digest of the complete local `Evidence` corpus; and
- a canonical SHA-256 digest of the trace payload, excluding the digest field itself.

Serialization uses sorted keys and compact JSON. Replay rejects missing or invalid trace digests and rejects a corpus digest mismatch before recomputing retrieval.

## Controlled Results

- Same-ID source content changes fail closed.
- Trace payload digest tampering fails closed.
- Existing successful replay remains deterministic.

## Decision

`ADAPT`

Retain corpus-bound replay as a local integrity control. It detects drift and accidental or local tampering; it does not establish that the corpus, authority metadata, or digest anchor is independently trusted.

## Remaining Risks

- The digest is not externally anchored or signed by a protected authority.
- Authority and hierarchy fields remain caller-supplied.
- Historical source bytes are not stored by the trace itself.
- Digest coverage does not establish source truth.
