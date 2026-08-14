"""Synthetic transport metadata binding for local MCP experiments."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping


@dataclass(frozen=True)
class SyntheticTransportEnvelope:
    request_id: str
    audience: str
    task_id: str
    method: str
    parameters_hash: str
    response_hash: str = ""

    @classmethod
    def request(
        cls,
        *,
        request_id: str,
        audience: str,
        task_id: str,
        method: str,
        parameters: Mapping[str, str],
    ) -> SyntheticTransportEnvelope:
        if not all(value.strip() for value in (request_id, audience, task_id, method)):
            raise ValueError("Transport envelope identity fields are required")
        return cls(request_id, audience, task_id, method, _digest(parameters))

    def bind_response(self, response: Mapping[str, str]) -> SyntheticTransportEnvelope:
        return SyntheticTransportEnvelope(
            self.request_id,
            self.audience,
            self.task_id,
            self.method,
            self.parameters_hash,
            _digest(response),
        )

    def verify_response(
        self,
        response_envelope: SyntheticTransportEnvelope,
        *,
        audience: str,
        task_id: str,
    ) -> None:
        if response_envelope.request_id != self.request_id:
            raise ValueError("Transport response request ID does not match")
        if response_envelope.audience != audience or response_envelope.task_id != task_id:
            raise ValueError("Transport response audience or task does not match")
        if response_envelope.parameters_hash != self.parameters_hash:
            raise ValueError("Transport response parameters do not match")
        if not response_envelope.response_hash:
            raise ValueError("Transport response is incomplete")


def _digest(value: Mapping[str, str]) -> str:
    payload = json.dumps(dict(sorted(value.items())), separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
