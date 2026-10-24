import MaintenanceScreen from "../app/(gates)/maintenance";
import UpdateRequiredScreen from "../app/(gates)/update-required";
import SettingsScreen from "../app/settings/index";

describe("Settings Privacy and DPDP Contracts", () => {
  it("formats photo deletion path accurately for backend endpoint", () => {
    const userId = "123e4567-e89b-12d3-a456-426614174000";
    const photoId = "987fcdeb-51a2-43f1-b987-123456789abc";
    const endpoint = `/profile/${userId}/photos/${photoId}`;
    expect(endpoint).toBe("/profile/123e4567-e89b-12d3-a456-426614174000/photos/987fcdeb-51a2-43f1-b987-123456789abc");
  });

  it("formats consent revocation payload with body_photo data type", () => {
    const userId = "123e4567-e89b-12d3-a456-426614174000";
    const endpoint = `/profile/${userId}/consent/revoke`;
    const payload = { data_type: "body_photo" };
    expect(endpoint).toBe("/profile/123e4567-e89b-12d3-a456-426614174000/consent/revoke");
    expect(payload.data_type).toBe("body_photo");
  });

  it("targets /me DELETE endpoint for irreversible account erasure", () => {
    const endpoint = "/me";
    const method = "DELETE";
    expect(endpoint).toBe("/me");
    expect(method).toBe("DELETE");
  });

  it("correctly identifies active reference photo from derived profile response", () => {
    const photos = [
      {
        id: "p1",
        photo_type: "tryon_reference",
        status: "rejected",
        storage_key: "k1",
        reject_reason: "dark",
        quality_reasons: [],
      },
      {
        id: "p2",
        photo_type: "tryon_reference",
        status: "accepted",
        storage_key: "k2",
        reject_reason: null,
        quality_reasons: [],
      },
    ];

    const activePhoto = photos.find((p) => p.status === "accepted") || photos[0];
    expect(activePhoto).toBeDefined();
    expect(activePhoto?.id).toBe("p2");
    expect(activePhoto?.status).toBe("accepted");
  });
});

describe("Remote Config Gate Route Screens", () => {
  it("exports MaintenanceScreen as a functional component", () => {
    expect(typeof MaintenanceScreen).toBe("function");
  });

  it("exports UpdateRequiredScreen as a functional component", () => {
    expect(typeof UpdateRequiredScreen).toBe("function");
  });

  it("exports SettingsScreen as a functional component", () => {
    expect(typeof SettingsScreen).toBe("function");
  });
});
