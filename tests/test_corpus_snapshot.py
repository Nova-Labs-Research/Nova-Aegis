from __future__ import annotations

import pytest

from nova_aegis import CorpusSnapshot, Evidence


def test_snapshot_round_trip_restores_historical_order() -> None:
    documents = (
        Evidence(source_id="DOC-2", title="Second", text="Beta"),
        Evidence(source_id="DOC-1", title="First", text="Alpha"),
    )
    snapshot = CorpusSnapshot.create(documents, snapshot_version=2)
    restored = CorpusSnapshot.from_dict(snapshot.to_dict())

    assert [document.source_id for document in restored.restore(minimum_version=2)] == [
        "DOC-1",
        "DOC-2",
    ]


def test_snapshot_rejects_rollback_and_content_tampering() -> None:
    snapshot = CorpusSnapshot.create(
        [Evidence(source_id="DOC-1", title="First", text="Alpha")],
        snapshot_version=2,
    )
    with pytest.raises(ValueError, match="older"):
        snapshot.restore(minimum_version=3)

    forged = snapshot.to_dict()
    forged["documents"][0]["text"] = "Forged"
    with pytest.raises(ValueError, match="digest"):
        CorpusSnapshot.from_dict(forged).restore()
