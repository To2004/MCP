"""Pseudonyms for values the log must compare but should not show.

A session id, a recipient or a call's arguments are logged as an HMAC-SHA256 of the value
under a key from the environment: equal values give equal pseudonyms, so a dimension can
still ask "seen before?", and a log reader cannot recover a value by hashing guesses.

Without a key the pseudonym is a plain SHA-256. That is still one-way for random values
such as session ids (the MCP spec requires them to be unguessable), but an e-mail address
or a repository name can be recovered by hashing candidates — so set the key whenever the
log is written without message bodies.
"""

from __future__ import annotations

import hashlib
import hmac
import os

PSEUDONYM_CHARS = 32  # 128 bits: no collision at any realistic log size


class Pseudonymizer:
    """Turns a value into its pseudonym, keyed when a key was given."""

    def __init__(self, key: bytes | None = None) -> None:
        self._key = key

    @classmethod
    def from_env(cls, env_var: str | None) -> Pseudonymizer:
        """Keyed by the value of ``env_var`` when it is set; unkeyed otherwise."""
        value = os.environ.get(env_var) if env_var else None
        return cls(value.encode() if value else None)

    @property
    def keyed(self) -> bool:
        """True when pseudonyms are HMACs; False when they are plain SHA-256."""
        return self._key is not None

    def of(self, value: str) -> str:
        """The pseudonym of ``value``: the same value always gives the same string."""
        data = value.encode()
        if self._key is None:
            return hashlib.sha256(data).hexdigest()[:PSEUDONYM_CHARS]
        return hmac.new(self._key, data, hashlib.sha256).hexdigest()[:PSEUDONYM_CHARS]
