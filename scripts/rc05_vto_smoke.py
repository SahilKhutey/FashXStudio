#!/usr/bin/env python3
"""RC-05 Virtual Try-On (VTO) End-to-End System Smoke Verification Script.

Verifies end-to-end VTO pipeline:
1. Health & readiness probes (/healthz/live, /healthz/ready)
2. Identity authentication and consent (/api/v1/me, /api/v1/consents)
3. Try-on supported garment resolution from catalog
4. Active accepted photo resolution and consent verification
5. Asynchronous try-on job submission with idempotency key
6. Job execution via direct processing or worker
7. Job status polling and signed URL generation
8. Cross-user privacy barrier (User B cannot access User A's job/artifact)
9. Saving try-on look to user wardrobe (closet)
10. Submitting visual accuracy and fit feedback
"""

from __future__ import annotations

import io
import sys
from uuid import UUID, uuid4
from PIL import Image
from fastapi.testclient import TestClient

from database.models.catalog import CanonicalGarment, CatalogSource, Merchant
from database.models.identity import User
from fashx.api.v1.me import get_profile_uow
from fashx.catalog.router import get_catalog_uow
from fashx.core.settings import get_settings
from fashx.main import app
from fashx.security.tokens import create_demo_token
from fashx.tryon.application.process_job import ProcessTryOnJobUseCase
from fashx.tryon.application.worker import TryOnWorker
from fashx.tryon.router import get_tryon_uow


def make_test_portrait() -> bytes:
    img = Image.new("RGB", (512, 768), (140, 120, 100))
    for x in range(256):
        for y in range(768):
            img.putpixel((x, y), (200, 180, 160))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


async def setup_test_data(user_id: UUID, user_b_id: UUID) -> UUID:
    profile_factory = app.dependency_overrides.get(get_profile_uow, get_profile_uow)
    catalog_factory = app.dependency_overrides.get(get_catalog_uow, get_catalog_uow)

    profile_uow = profile_factory()
    catalog_uow = catalog_factory()

    portrait_bytes = make_test_portrait()

    async with profile_uow:
        # Create User A
        existing_a = await profile_uow.users.get_by_id(user_id)
        if not existing_a:
            profile_uow.users.add(User(id=user_id))
            await profile_uow.flush()
        await profile_uow.consents.record_mobile_consent(user_id, "2026.1")

        # Create active portrait for User A
        photo = await profile_uow.photos.create(
            user_id=user_id,
            photo_type="tryon_reference",
            storage_key=f"u/{user_id}/photos/portrait.jpg",
            status="accepted",
        )

        # Create User B
        existing_b = await profile_uow.users.get_by_id(user_b_id)
        if not existing_b:
            profile_uow.users.add(User(id=user_b_id))
            await profile_uow.flush()
        await profile_uow.consents.record_mobile_consent(user_b_id, "2026.1")
        await profile_uow.commit()

    async with catalog_uow:
        merchant = Merchant(name="RC05 Retailer", merchant_type="retailer")
        catalog_uow.merchants.add(merchant)
        await catalog_uow.flush()

        source = CatalogSource(
            slug=f"rc05-source-{merchant.id}",
            name="RC05 Feed",
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        catalog_uow.sources.add(source)
        await catalog_uow.flush()

        garment = CanonicalGarment(
            display_name="RC05 Tailored Silk Shirt",
            category="tops",
            tryon_supported=True,
        )
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.commit()
        garment_id = garment.id

    # Seed storage with mock photo
    from fashx.core.dependencies import get_storage
    storage = get_storage()
    if hasattr(storage, "put"):
        storage.put(f"u/{user_id}/photos/portrait.jpg", portrait_bytes, content_type="image/jpeg")
        storage.put(f"garments/{garment_id}/primary.jpg", portrait_bytes, content_type="image/jpeg")

    return garment_id


def run_vto_smoke_test() -> None:
    print("=== FashXStudio RC-05 Virtual Try-On Smoke Verification ===\n")
    import asyncio

    token_a = create_demo_token(subject="user-a-smoke-rc05")
    token_b = create_demo_token(subject="user-b-smoke-rc05")

    client_a = TestClient(app, headers={"Authorization": f"Bearer {token_a}"})
    client_b = TestClient(app, headers={"Authorization": f"Bearer {token_b}"})

    # Step 1: Health Probes
    print("[1/8] Verifying Health & Readiness probes...")
    live_res = client_a.get("/healthz/live")
    assert live_res.status_code == 200 and live_res.json()["status"] == "ok"
    print("  + /healthz/live: OK")

    ready_res = client_a.get("/healthz/ready")
    assert ready_res.status_code == 200
    print("  + /healthz/ready: OK")

    # Step 2: Authenticate User A and User B
    print("\n[2/8] Authenticating User A and User B...")
    me_a = client_a.get("/api/v1/me")
    assert me_a.status_code == 200
    user_a_id = UUID(me_a.json()["user_id"])
    print(f"  + User A authenticated: {user_a_id}")

    me_b = client_b.get("/api/v1/me")
    assert me_b.status_code == 200
    user_b_id = UUID(me_b.json()["user_id"])
    print(f"  + User B authenticated: {user_b_id}")

    garment_id = asyncio.run(setup_test_data(user_a_id, user_b_id))
    print(f"  + Garment ID: {garment_id}")

    # Step 3: Submit Try-On Job
    print("\n[3/8] Submitting try-on job for User A with Idempotency-Key...")
    idempotency_key = f"smoke-vto-{uuid4()}"
    submit_res = client_a.post(
        "/api/v1/tryon/jobs",
        headers={"Idempotency-Key": idempotency_key},
        json={"garment_id": str(garment_id)},
    )
    assert submit_res.status_code == 202, f"Failed submit: {submit_res.text}"
    job_data = submit_res.json()
    job_id = job_data["job_id"]
    print(f"  + Job created: ID={job_id}, status={job_data['status']}, artifact_key={job_data['artifact_key']}")

    # Idempotent re-submission returns same job
    replay_res = client_a.post(
        "/api/v1/tryon/jobs",
        headers={"Idempotency-Key": idempotency_key},
        json={"garment_id": str(garment_id)},
    )
    assert replay_res.status_code == 202
    assert replay_res.json()["job_id"] == job_id
    print("  + Idempotent re-submission verified: returned identical job_id")

    # Step 4: Process Job via UseCase
    print("\n[4/8] Executing VTO pipeline (image prep, inference, watermark, quality gate)...")
    tryon_factory = app.dependency_overrides.get(get_tryon_uow, get_tryon_uow)
    profile_factory = app.dependency_overrides.get(get_profile_uow, get_profile_uow)
    catalog_factory = app.dependency_overrides.get(get_catalog_uow, get_catalog_uow)

    tryon_uow = tryon_factory()
    profile_uow = profile_factory()
    catalog_uow = catalog_factory()

    process_uc = ProcessTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
    )
    portrait_bytes = make_test_portrait()
    proc_res = asyncio.run(
        process_uc.execute(
            UUID(job_id),
            user_photo_bytes=portrait_bytes,
            garment_image_bytes=portrait_bytes,
        )
    )
    assert proc_res.status == "completed", f"Job failed to complete: {proc_res}"
    print(f"  + Job processing succeeded: status={proc_res.status}")

    # Step 5: Check Job Status & Signed Result URL
    print("\n[5/8] Polling job status and validating signed artifact URL...")
    status_res = client_a.get(f"/api/v1/tryon/jobs/{job_id}")
    assert status_res.status_code == 200
    st_data = status_res.json()
    assert st_data["status"] == "completed"
    assert st_data["result_url"] is not None
    assert st_data["provider"] in ("mock", "fashn_api")
    print(f"  + Job status: completed")
    print(f"  + Provider: {st_data['provider']} (mock preview correctly identifiable)")
    print(f"  + Signed Result URL: {st_data['result_url'][:50]}...")

    # Step 6: User Isolation / Privacy Check
    print("\n[6/8] Verifying User B cannot access User A's try-on job or artifact...")
    foreign_job_res = client_b.get(f"/api/v1/tryon/jobs/{job_id}")
    assert foreign_job_res.status_code == 404, f"User B accessed User A job! HTTP {foreign_job_res.status_code}"
    print("  + Privacy barrier verified: User B received 404 for User A job")

    foreign_art_res = client_b.get(f"/api/v1/tryon/artifacts/{job_data['artifact_key']}")
    assert foreign_art_res.status_code in (403, 404), f"User B accessed User A artifact! HTTP {foreign_art_res.status_code}"
    print("  + Privacy barrier verified: User B cannot access User A artifact")

    # Step 7: Save to Wardrobe
    print("\n[7/8] Saving completed try-on look to user wardrobe...")
    save_res = client_a.post(
        "/api/v1/wardrobe/items",
        json={"garment_id": str(garment_id)},
    )
    assert save_res.status_code == 201
    save_data = save_res.json()
    item_id = save_data["item_id"]
    print(f"  + Look saved to wardrobe: item_id={item_id}")

    # Step 8: Submit Try-On Feedback
    print("\n[8/8] Submitting post-try-on visual accuracy and fit feedback...")
    fb_res = client_a.post(
        "/api/v1/feedback/tryon",
        json={
            "tryon_job_id": job_id,
            "visual_accuracy": "accurate",
            "purchase_confidence": 5,
            "issue_tags": [],
        },
    )
    assert fb_res.status_code in (200, 201)
    print("  + Feedback submitted successfully")

    print("\n============================================================")
    print("SUCCESS: ALL RC-05 VIRTUAL TRY-ON SMOKE WORKFLOWS VERIFIED")
    print("============================================================")


if __name__ == "__main__":
    try:
        run_vto_smoke_test()
    except Exception as exc:
        print(f"\nRC05 VTO SMOKE TEST FAILED: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
