from __future__ import annotations

import pytest

from nova_aegis import SyntheticTransportEnvelope


def test_transport_envelope_binds_response_to_request() -> None:
    request = SyntheticTransportEnvelope.request(
        request_id="REQ-1",
        audience="reviewer",
        task_id="TASK-1",
        method="tools/read",
        parameters={"path": "local.txt"},
    )
    response = request.bind_response({"status": "ok"})
    request.verify_response(response, audience="reviewer", task_id="TASK-1")


def test_transport_envelope_rejects_cross_task_response() -> None:
    request = SyntheticTransportEnvelope.request(
        request_id="REQ-1",
        audience="reviewer",
        task_id="TASK-1",
        method="tools/read",
        parameters={"path": "local.txt"},
    )
    response = request.bind_response({"status": "ok"})
    with pytest.raises(ValueError, match="task"):
        request.verify_response(response, audience="reviewer", task_id="TASK-2")
