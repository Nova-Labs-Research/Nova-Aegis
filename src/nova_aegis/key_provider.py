"""Injectable synthetic authority for recovery-journal key material."""

from __future__ import annotations

from typing import Protocol


class JournalKeyProvider(Protocol):
    def get(self, key_id: str) -> bytes | None: ...

    def active(self) -> tuple[str, bytes] | None: ...

    def rotate(self, key_id: str, secret: bytes, *, authority: str) -> None: ...

    def retire(self, key_id: str, *, authority: str) -> None: ...


class LocalJournalKeyProvider:
    """Process-local key provider for synthetic testing, not protected custody."""

    def __init__(
        self,
        keys: dict[str, bytes] | None = None,
        *,
        active_key_id: str | None = None,
        rotation_authority: str = "synthetic-key-admin",
    ) -> None:
        self._keys = {key_id: bytes(secret) for key_id, secret in (keys or {}).items()}
        self._active_key_id = active_key_id or (next(iter(self._keys)) if self._keys else None)
        self._rotation_authority = rotation_authority
        if self._active_key_id is not None and self._active_key_id not in self._keys:
            raise ValueError("Active journal key is not trusted")

    def get(self, key_id: str) -> bytes | None:
        return self._keys.get(key_id)

    def active(self) -> tuple[str, bytes] | None:
        if self._active_key_id is None:
            return None
        return self._active_key_id, self._keys[self._active_key_id]

    def rotate(self, key_id: str, secret: bytes, *, authority: str) -> None:
        self._require_authority(authority)
        if not isinstance(key_id, str) or not key_id.strip() or not secret:
            raise ValueError("Journal key rotation requires a non-empty key ID and secret")
        self._keys[key_id] = bytes(secret)
        self._active_key_id = key_id

    def retire(self, key_id: str, *, authority: str) -> None:
        self._require_authority(authority)
        if key_id == self._active_key_id:
            raise ValueError("Cannot retire the active journal key")
        self._keys.pop(key_id, None)

    def _require_authority(self, authority: str) -> None:
        if authority != self._rotation_authority:
            raise PermissionError("Journal key lifecycle authority is invalid")
