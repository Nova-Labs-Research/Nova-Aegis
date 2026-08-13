from __future__ import annotations

import pytest

from nova_aegis import (
    FoundryLocalProvider,
    InferenceUnavailable,
    ModelManifest,
    ProviderState,
)


@pytest.fixture
def manifest() -> ModelManifest:
    return ModelManifest(model_id="local-test-model", artifact_hash="sha256:test")


def test_provider_requires_explicit_offline_provisioning(manifest: ModelManifest) -> None:
    provider = FoundryLocalProvider()

    with pytest.raises(PermissionError, match="Network provisioning is disabled"):
        provider.provision(manifest, allow_network=True)

    assert provider.state is ProviderState.UNPROVISIONED


def test_provider_lifecycle_runs_with_injected_local_runtime(manifest: ModelManifest) -> None:
    provider = FoundryLocalProvider(inference_fn=lambda prompt: f"local:{prompt}")

    provider.provision(manifest)
    assert provider.state is ProviderState.PROVISIONED

    provider.load()
    assert provider.state is ProviderState.READY

    result = provider.infer("status")

    assert result.provider == "foundry_local"
    assert result.model_id == "local-test-model"
    assert result.text == "local:status"
    assert provider.state is ProviderState.READY

    provider.unload()
    assert provider.state is ProviderState.UNLOADED


def test_provider_cannot_load_before_provisioning() -> None:
    provider = FoundryLocalProvider()

    with pytest.raises(InferenceUnavailable, match="UNPROVISIONED"):
        provider.load()


def test_provider_without_runtime_does_not_fake_inference(manifest: ModelManifest) -> None:
    provider = FoundryLocalProvider()
    provider.provision(manifest)
    provider.load()

    with pytest.raises(InferenceUnavailable, match="not available"):
        provider.infer("status")

    assert provider.state is ProviderState.READY


def test_provider_rejects_invalid_manifest() -> None:
    provider = FoundryLocalProvider()

    with pytest.raises(ValueError, match="model_id"):
        provider.provision(ModelManifest(model_id="", artifact_hash="sha256:test"))
