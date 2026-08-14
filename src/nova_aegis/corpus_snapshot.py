"""Versioned local corpus snapshots for retrieval replay experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping

from .core import Evidence


@dataclass(frozen=True)
class CorpusSnapshot:
    snapshot_version: int
    corpus_digest: str
    documents: tuple[Evidence, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_version": self.snapshot_version,
            "corpus_digest": self.corpus_digest,
            "documents": [asdict(document) for document in self.documents],
        }

    @classmethod
    def create(
        cls, documents: Iterable[Evidence], *, snapshot_version: int
    ) -> CorpusSnapshot:
        if snapshot_version < 1:
            raise ValueError("Corpus snapshot version must be positive")
        ordered = tuple(sorted(documents, key=lambda document: document.source_id))
        snapshot = cls(snapshot_version, "", ordered)
        return cls(snapshot_version, snapshot.calculate_digest(), ordered)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> CorpusSnapshot:
        try:
            documents = tuple(
                Evidence(
                    source_id=str(item["source_id"]),
                    title=str(item["title"]),
                    text=str(item["text"]),
                    revision_id=str(item.get("revision_id", "unknown")),
                    authority=str(item.get("authority", "unclassified")),
                    claim_group=item.get("claim_group"),
                    claim=item.get("claim"),
                    status=str(item.get("status", "current")),
                    provenance_verified=bool(item.get("provenance_verified", False)),
                    hierarchy=tuple(item.get("hierarchy", ())),
                )
                for item in value["documents"]
            )
            return cls(int(value["snapshot_version"]), str(value["corpus_digest"]), documents)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Corpus snapshot has an invalid serialized shape") from error

    def calculate_digest(self) -> str:
        payload = json.dumps(
            [asdict(document) for document in self.documents],
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def restore(self, *, minimum_version: int = 1) -> tuple[Evidence, ...]:
        if self.snapshot_version < minimum_version:
            raise ValueError("Corpus snapshot is older than the required version")
        if self.calculate_digest() != self.corpus_digest:
            raise ValueError("Corpus snapshot digest does not match")
        return self.documents
