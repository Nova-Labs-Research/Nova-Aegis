from __future__ import annotations

from dataclasses import replace

import pytest

from nova_aegis import ExternalReceiptError, LocalExternalReceiptRegistry


def test_receipt_registry_binds_audience_parameters_and_revocation() -> None:
    registry = LocalExternalReceiptRegistry(secret=b"receipt-secret")
    receipt = registry.create(
        task_id="task-1",
        tool_name="synthetic-status",
        user_id="operator-1",
        audience="https://gateway.example/mcp",
        status="completed",
        parameters_hash="params-1",
        result={"status": "ok"},
    )

    assert registry.verify(
        receipt.receipt_id,
        task_id="task-1",
        tool_name="synthetic-status",
        user_id="operator-1",
        audience="https://gateway.example/mcp",
        parameters_hash="params-1",
        result={"status": "ok"},
    ) == receipt

    with pytest.raises(ExternalReceiptError, match="match"):
        registry.verify(
            receipt.receipt_id,
            task_id="task-1",
            tool_name="synthetic-status",
            user_id="operator-1",
            audience="https://other.example/mcp",
            parameters_hash="params-1",
            result={"status": "ok"},
        )

    registry.revoke(receipt.receipt_id)
    with pytest.raises(ExternalReceiptError, match="revoked"):
        registry.verify(
            receipt.receipt_id,
            task_id="task-1",
            tool_name="synthetic-status",
            user_id="operator-1",
            audience="https://gateway.example/mcp",
            parameters_hash="params-1",
            result={"status": "ok"},
        )


def test_receipt_registry_rejects_conflicting_duplicate_id() -> None:
    registry = LocalExternalReceiptRegistry(secret=b"receipt-secret")
    receipt = registry.create(
        task_id="task-1",
        tool_name="synthetic-status",
        user_id="operator-1",
        audience="https://gateway.example/mcp",
        status="completed",
        parameters_hash="params-1",
        result={"status": "ok"},
    )
    conflicting = replace(receipt, result_hash="forged-result")

    with pytest.raises(ExternalReceiptError, match="conflicting"):
        registry.register(conflicting)
