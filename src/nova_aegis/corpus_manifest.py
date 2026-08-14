"""Synthetic signed corpus manifests for local retrieval experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import hmac
import json
from typing import Any, Iterable, Mapping, Protocol


class ManifestKeyProvider(Protocol):
    def get(self, key_id: str) -> bytes | None: ...

    def active(self) -> tuple[str, bytes] | None: ...


@dataclass(frozen=True)
class CorpusManifest:
    manifest_version: int
    corpus_digest: str
    source_ids: tuple[str, ...]
    key_id: str
    signature: str

    def payload(self) -> dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "corpus_digest": self.corpus_digest,
            "source_ids": self.source_ids,
            "key_id": self.key_id,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.payload(), "signature": self.signature}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> CorpusManifest:
        try:
            return cls(
                manifest_version=int(value["manifest_version"]),
                corpus_digest=str(value["corpus_digest"]),
                source_ids=tuple(str(source_id) for source_id in value["source_ids"]),
                key_id=str(value["key_id"]),
                signature=str(value["signature"]),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Corpus manifest has an invalid serialized shape") from error

    @classmethod
    def create(
        cls,
        documents: Iterable[Any],
        key_provider: ManifestKeyProvider,
        *,
        manifest_version: int,
    ) -> CorpusManifest:
        if manifest_version < 1:
            raise ValueError("Corpus manifest version must be positive")
        documents = tuple(documents)
        active = key_provider.active()
        if active is None:
            raise ValueError("Corpus manifest requires an active signing key")
        key_id, secret = active
        source_ids = tuple(sorted(str(document.source_id) for document in documents))
        corpus_digest = calculate_corpus_digest(documents)
        unsigned = cls(manifest_version, corpus_digest, source_ids, key_id, "")
        signature = _sign(unsigned.payload(), secret)
        return cls(manifest_version, corpus_digest, source_ids, key_id, signature)

    def verify(
        self,
        documents: Iterable[Any],
        key_provider: ManifestKeyProvider,
        *,
        minimum_version: int = 1,
    ) -> None:
        documents = tuple(documents)
        if self.manifest_version < minimum_version:
            raise ValueError("Corpus manifest is older than the required version")
        secret = key_provider.get(self.key_id)
        if secret is None:
            raise ValueError("Corpus manifest signing key is not trusted")
        expected_signature = _sign(self.payload(), secret)
        if not hmac.compare_digest(self.signature, expected_signature):
            raise ValueError("Corpus manifest signature is invalid")
        current_source_ids = tuple(sorted(str(document.source_id) for document in documents))
        if current_source_ids != self.source_ids:
            raise ValueError("Corpus manifest source identity does not match")
        if calculate_corpus_digest(documents) != self.corpus_digest:
            raise ValueError("Corpus manifest corpus digest does not match")


def calculate_corpus_digest(documents: Iterable[Any]) -> str:
    serialized_documents = [
        asdict(document) if hasattr(document, "__dataclass_fields__") else dict(document)
        for document in sorted(documents, key=lambda item: str(item.source_id))
    ]
    payload = json.dumps(
        serialized_documents, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sign(payload: Mapping[str, Any], secret: bytes) -> str:
    serialized = json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hmac.new(secret, serialized, hashlib.sha256).hexdigest()
