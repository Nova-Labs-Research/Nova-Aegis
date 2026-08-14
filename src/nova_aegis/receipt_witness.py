"""Synthetic independent-witness boundary for receipt experiments."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
from typing import Mapping

from .receipt_store import ExternalExecutionReceipt, ExternalReceiptError


@dataclass(frozen=True)
class ReceiptWitnessAttestation:
    receipt_id: str
    issuer_id: str
    witness_id: str
    receipt_digest: str
    signature: str


class LocalReceiptWitness:
    """Separate local signer used to test receipt-witness separation."""

    def __init__(self, *, witness_id: str, secret: bytes) -> None:
        if not witness_id.strip() or not secret:
            raise ValueError("Receipt witness identity and secret are required")
        self.witness_id = witness_id
        self._secret = secret
        self._attestations: dict[str, ReceiptWitnessAttestation] = {}

    def attest(
        self,
        receipt: ExternalExecutionReceipt,
        *,
        issuer_id: str,
    ) -> ReceiptWitnessAttestation:
        if not issuer_id.strip():
            raise ValueError("Receipt issuer identity is required")
        if issuer_id == self.witness_id:
            raise ExternalReceiptError("Receipt issuer and witness must be distinct")
        receipt_digest = digest_receipt(receipt)
        attestation = ReceiptWitnessAttestation(
            receipt.receipt_id,
            issuer_id,
            self.witness_id,
            receipt_digest,
            self._sign(receipt.receipt_id, issuer_id, self.witness_id, receipt_digest),
        )
        existing = self._attestations.get(receipt.receipt_id)
        if existing is not None and existing != attestation:
            raise ExternalReceiptError("Receipt witness has conflicting attestations")
        self._attestations[receipt.receipt_id] = attestation
        return attestation

    def verify(
        self,
        attestation: ReceiptWitnessAttestation,
        receipt: ExternalExecutionReceipt,
        *,
        issuer_id: str,
    ) -> None:
        if attestation.receipt_id != receipt.receipt_id:
            raise ExternalReceiptError("Receipt witness does not match receipt")
        if attestation.issuer_id != issuer_id:
            raise ExternalReceiptError("Receipt witness issuer does not match")
        if attestation.witness_id != self.witness_id:
            raise ExternalReceiptError("Receipt witness identity does not match")
        if attestation.receipt_digest != digest_receipt(receipt):
            raise ExternalReceiptError("Receipt witness digest does not match")
        expected = self._sign(
            attestation.receipt_id,
            attestation.issuer_id,
            attestation.witness_id,
            attestation.receipt_digest,
        )
        if not hmac.compare_digest(attestation.signature, expected):
            raise ExternalReceiptError("Receipt witness signature is invalid")

    def _sign(self, *parts: str) -> str:
        payload = "|".join(parts).encode("utf-8")
        return hmac.new(self._secret, payload, hashlib.sha256).hexdigest()


def digest_receipt(receipt: ExternalExecutionReceipt) -> str:
    payload: Mapping[str, object] = {
        "receipt_id": receipt.receipt_id,
        "task_id": receipt.task_id,
        "tool_name": receipt.tool_name,
        "user_id": receipt.user_id,
        "audience": receipt.audience,
        "status": receipt.status,
        "parameters_hash": receipt.parameters_hash,
        "result_hash": receipt.result_hash,
        "issued_at": receipt.issued_at,
        "expires_at": receipt.expires_at,
        "signature": receipt.signature,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
