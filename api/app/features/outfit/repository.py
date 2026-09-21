from collections.abc import Iterable

from .models import Outfit


class OutfitRepository:
    def __init__(self, outfits: Iterable[Outfit] = ()) -> None:
        self._outfits = list(outfits)

    def add(self, outfit: Outfit) -> None:
        self._outfits.append(outfit)

    def get(self, outfit_id: str) -> Outfit | None:
        return next((o for o in self._outfits if o.outfit_id == outfit_id), None)

    def replace(self, outfit: Outfit) -> None:
        self._outfits[
            self._outfits.index(next(o for o in self._outfits if o.outfit_id == outfit.outfit_id))
        ] = outfit
