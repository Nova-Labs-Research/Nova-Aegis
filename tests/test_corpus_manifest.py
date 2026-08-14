from __future__ import annotations

import pytest

from nova_aegis import CorpusManifest, Evidence, LocalJournalKeyProvider


@pytest.fixture
def documents() -> tuple[Evidence, ...]:
    return (
        Evidence(source_id="DOC-2", title="Second", text="Beta"),
        Evidence(source_id="DOC-1", title="First", text="Alpha"),
    )


def test_manifest_signs_and_verifies_canonical_corpus(documents) -> None:
    provider = LocalJournalKeyProvider({"manifest-v1": b"manifest-secret"})

    manifest = CorpusManifest.create(documents, provider, manifest_version=1)
    restored = CorpusManifest.from_dict(manifest.to_dict())
    restored.verify(tuple(reversed(documents)), provider)

    assert restored.source_ids == ("DOC-1", "DOC-2")
    assert restored.signature


def test_manifest_rejects_tampering_unknown_key_rollback_and_corpus_drift(documents) -> None:
    provider = LocalJournalKeyProvider({"manifest-v1": b"manifest-secret"})
    manifest = CorpusManifest.create(documents, provider, manifest_version=2)

    forged = manifest.to_dict()
    forged["corpus_digest"] = "0" * 64
    with pytest.raises(ValueError, match="signature"):
        CorpusManifest.from_dict(forged).verify(documents, provider)

    with pytest.raises(ValueError, match="older"):
        manifest.verify(documents, provider, minimum_version=3)

    unknown_key = CorpusManifest(
        manifest.manifest_version,
        manifest.corpus_digest,
        manifest.source_ids,
        "retired-key",
        manifest.signature,
    )
    with pytest.raises(ValueError, match="trusted"):
        unknown_key.verify(documents, provider)

    changed = (*documents, Evidence(source_id="DOC-3", title="Third", text="Gamma"))
    with pytest.raises(ValueError, match="source identity"):
        manifest.verify(changed, provider)
