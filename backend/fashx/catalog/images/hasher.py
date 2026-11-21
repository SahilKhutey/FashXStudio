"""Cryptographic and perceptual image hashing algorithms."""

from __future__ import annotations

import hashlib
from io import BytesIO

from PIL import Image


class ImageHasher:
    """Computes exact SHA-256 hashes and difference perceptual hashes (dHash)."""

    DHASH_SIZE = 8
    HASH_VERSION = "v1"

    @classmethod
    def compute_sha256(cls, data: bytes) -> str:
        """Compute standard hex SHA-256 hash."""
        return hashlib.sha256(data).hexdigest()

    @classmethod
    def compute_dhash(cls, image_data: bytes | Image.Image, hash_size: int = DHASH_SIZE) -> str:
        """Compute perceptual difference hash (dHash) for visual similarity comparison.

        Resizes to (hash_size + 1, hash_size), converts to grayscale, and compares
        adjacent pixels horizontally.
        """
        if isinstance(image_data, bytes):
            img = Image.open(BytesIO(image_data))
        else:
            img = image_data

        try:
            # Resize to (width = hash_size + 1, height = hash_size)
            resized = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
            if hasattr(resized, "get_flattened_data"):
                pixels = list(resized.get_flattened_data())
            else:
                pixels = list(resized.getdata())

            difference: list[bool] = []
            for row in range(hash_size):
                row_start = row * (hash_size + 1)
                for col in range(hash_size):
                    pixel_left = pixels[row_start + col]
                    pixel_right = pixels[row_start + col + 1]
                    difference.append(pixel_left > pixel_right)

            decimal_value = 0
            for index, value in enumerate(difference):
                if value:
                    decimal_value += 2**index

            # Format as fixed-length hex string (64 bits = 16 hex characters for size 8)
            hex_length = (hash_size * hash_size) // 4
            return f"{decimal_value:0{hex_length}x}"
        finally:
            if isinstance(image_data, bytes):
                img.close()

    @classmethod
    def hamming_distance(cls, hash1: str, hash2: str) -> int:
        """Compute bitwise Hamming distance between two hex hashes."""
        try:
            val1 = int(hash1, 16)
            val2 = int(hash2, 16)
            xor_val = val1 ^ val2
            return bin(xor_val).count("1")
        except (ValueError, TypeError):
            return 999
