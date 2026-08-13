"""Provider-abstract local inference boundary for Nova Aegis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class ProviderState(str, Enum):
    UNPROVISIONED = "UNPROVISIONED"
    PROVISIONED = "PROVISIONED"
    LOADED = "LOADED"
    READY = "READY"
    INFER = "INFER"
    UNLOADED = "UNLOADED"


class InferenceUnavailable(RuntimeError):
    """Raised when local inference cannot safely be performed."""


@dataclass(frozen=True)
class ModelManifest:
    model_id: str
    artifact_hash: str


@dataclass(frozen=True)
class InferenceResult:
    provider: str
    model_id: str
    text: str


InferenceFunction = Callable[[str], str]


class InferenceProvider:
    """Provider-neutral lifecycle contract for local inference."""

    provider_name = "abstract"

    def provision(self, manifest: ModelManifest, *, allow_network: bool = False) -> None:
        raise NotImplementedError

    def load(self) -> None:
        raise NotImplementedError

    def infer(self, prompt: str) -> InferenceResult:
        raise NotImplementedError

    def unload(self) -> None:
        raise NotImplementedError


class FoundryLocalProvider(InferenceProvider):
    """Foundry Local adapter boundary with explicit offline provisioning."""

    provider_name = "foundry_local"

    def __init__(self, inference_fn: InferenceFunction | None = None) -> None:
        self._inference_fn = inference_fn
        self._manifest: ModelManifest | None = None
        self._state = ProviderState.UNPROVISIONED

    @property
    def state(self) -> ProviderState:
        return self._state

    @property
    def manifest(self) -> ModelManifest | None:
        return self._manifest

    def provision(self, manifest: ModelManifest, *, allow_network: bool = False) -> None:
        if not manifest.model_id.strip() or not manifest.artifact_hash.strip():
            raise ValueError("Model manifest requires model_id and artifact_hash")
        if allow_network:
            raise PermissionError(
                "Network provisioning is disabled; import verified artifacts explicitly"
            )
        self._manifest = manifest
        self._state = ProviderState.PROVISIONED

    def load(self) -> None:
        self._require_state(ProviderState.PROVISIONED)
        self._state = ProviderState.LOADED
        self._state = ProviderState.READY

    def infer(self, prompt: str) -> InferenceResult:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Inference prompt must be a non-empty string")
        self._require_state(ProviderState.READY)
        if self._manifest is None or self._inference_fn is None:
            raise InferenceUnavailable("Foundry Local model is not available for local inference")
        self._state = ProviderState.INFER
        try:
            text = self._inference_fn(prompt)
        finally:
            self._state = ProviderState.READY
        return InferenceResult(
            provider=self.provider_name,
            model_id=self._manifest.model_id,
            text=text,
        )

    def unload(self) -> None:
        if self._state not in {ProviderState.LOADED, ProviderState.READY}:
            raise InferenceUnavailable("Provider is not loaded")
        self._state = ProviderState.UNLOADED

    def _require_state(self, expected: ProviderState) -> None:
        if self._state is not expected:
            raise InferenceUnavailable(
                f"Provider state is {self._state.value}; expected {expected.value}"
            )
