import io
from uuid import uuid4

from PIL import Image

from api.app.catalog.deduplication.hasher import ImageHasher
from api.app.catalog.deduplication.matcher import GarmentMatcher, MatchConfidence


def create_test_image(color: tuple[int, int, int], pattern: bool = False) -> bytes:
    img = Image.new("RGB", (64, 64), color)
    if pattern:
        for x in range(32):
            for y in range(64):
                img.putpixel((x, y), (255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_image_hasher_exact_and_dhash() -> None:
    data1 = create_test_image((10, 20, 30))
    data2 = create_test_image((10, 20, 30))
    data_diff = create_test_image((200, 50, 50), pattern=True)

    exact1 = ImageHasher.exact_hash(data1)
    exact2 = ImageHasher.exact_hash(data2)
    exact_diff = ImageHasher.exact_hash(data_diff)

    assert exact1 == exact2
    assert exact1 != exact_diff

    dhash1 = ImageHasher.compute_dhash(data1)
    dhash2 = ImageHasher.compute_dhash(data2)
    dhash_diff = ImageHasher.compute_dhash(data_diff)

    assert dhash1 == dhash2
    dist_same = ImageHasher.hamming_distance(dhash1, dhash2)
    assert dist_same == 0

    dist_diff = ImageHasher.hamming_distance(dhash1, dhash_diff)
    assert dist_diff > 0


def test_garment_matcher_exact_hash_match() -> None:
    garment_id = uuid4()
    exact_hash = "abc123exact"

    result = GarmentMatcher.evaluate_match(
        candidate_title="Oxford Shirt",
        candidate_exact_hash=exact_hash,
        candidate_dhash="0000ffff0000ffff",
        existing_garment_id=garment_id,
        existing_title="Oxford Casual Shirt",
        existing_exact_hashes=[exact_hash],
        existing_dhashes=["0000ffff0000ffff"],
        same_brand=True,
    )
    assert result.confidence == MatchConfidence.EXACT
    assert result.matched_garment_id == garment_id
    assert result.score == 1.0


def test_garment_matcher_perceptual_hash_match() -> None:
    garment_id = uuid4()
    # dHash with 1-bit difference
    dhash1 = "0000ffff0000ffff"
    dhash2 = "0000ffff0000fffe"

    result = GarmentMatcher.evaluate_match(
        candidate_title="Different Title",
        candidate_exact_hash="candidate_hash",
        candidate_dhash=dhash1,
        existing_garment_id=garment_id,
        existing_title="Existing Item",
        existing_exact_hashes=["other_hash"],
        existing_dhashes=[dhash2],
        same_brand=True,
    )
    assert result.confidence == MatchConfidence.HIGH
    assert result.matched_garment_id == garment_id
    assert result.score >= 0.90


def test_garment_matcher_lexical_overlap_match() -> None:
    garment_id = uuid4()

    result = GarmentMatcher.evaluate_match(
        candidate_title="Men Slim Fit Cotton Linen Casual Shirt White",
        candidate_exact_hash=None,
        candidate_dhash=None,
        existing_garment_id=garment_id,
        existing_title="Men Slim Fit Cotton Linen Casual Shirt",
        existing_exact_hashes=[],
        existing_dhashes=[],
        same_brand=True,
    )
    assert result.confidence == MatchConfidence.HIGH
    assert result.matched_garment_id == garment_id
    assert result.score > 0.80
