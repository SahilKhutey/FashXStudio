from __future__ import annotations

import hashlib
import math
import os
import re


class FakeEmbedder:
    """Deterministic fake embedder for tests and local development.

    Produces repeatable, unit-normalized 512-dim vectors from image bytes or text
    without downloading neural network weights. Refuses to run in production.
    """

    model_id = "mock-fake-512"
    dim = 512

    def __init__(self) -> None:
        env = os.getenv("ENV", "dev").lower()
        if env not in ("dev", "test", "local"):
            raise RuntimeError(
                f"FakeEmbedder is strictly forbidden in environment '{env}' "
                "(only 'dev', 'test', and 'local' allowed)."
            )

    def _token_vector(self, token: str) -> list[float]:
        raw = token.strip().lower().encode("utf-8")
        vec: list[float] = []
        seed = raw
        while len(vec) < self.dim:
            digest = hashlib.sha256(seed).digest()
            for i in range(0, 32, 4):
                val = int.from_bytes(digest[i : i + 4], byteorder="big", signed=True) / (2**31)
                vec.append(val)
                if len(vec) >= self.dim:
                    break
            seed = digest

        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [float(x / norm) for x in vec]

    def _hash_to_vector(self, data: bytes | str) -> list[float]:
        if isinstance(data, bytes):
            digest = hashlib.sha256(data).hexdigest()
            return self._token_vector(digest)

        tokens = [t.strip().lower() for t in re.split(r"\W+", data) if t.strip()]
        if not tokens:
            return self._token_vector("empty")

        accum = [0.0] * self.dim
        for tok in tokens:
            t_vec = self._token_vector(tok)
            for i in range(self.dim):
                accum[i] += t_vec[i]

        norm = math.sqrt(sum(x * x for x in accum)) or 1.0
        return [float(x / norm) for x in accum]

    def embed_images(self, images: list[bytes]) -> list[list[float]]:
        return [self._hash_to_vector(b) for b in images]

    def embed_text(self, texts: list[str]) -> list[list[float]]:
        return [self._hash_to_vector(t) for t in texts]
