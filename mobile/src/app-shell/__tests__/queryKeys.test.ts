import { queryKeys } from "../queryKeys";

describe("queryKeys", () => {
  it("isolates me query key per user ID", () => {
    expect(queryKeys.me("user-a")).toEqual(["me", "user-a"]);
    expect(queryKeys.me("user-b")).toEqual(["me", "user-b"]);
    expect(queryKeys.me(null)).toEqual(["me", null]);
    expect(queryKeys.me("user-a")).not.toEqual(queryKeys.me("user-b"));
  });

  it("isolates feed query key per user ID", () => {
    expect(queryKeys.feed("user-a")).toEqual(["feed", "user-a"]);
    expect(queryKeys.feed("user-b")).toEqual(["feed", "user-b"]);
    expect(queryKeys.feed("user-a")).not.toEqual(queryKeys.feed("user-b"));
  });

  it("isolates garment query key per user and garment ID", () => {
    expect(queryKeys.garment("user-a", "g-1")).toEqual(["garment", "user-a", "g-1"]);
    expect(queryKeys.garment("user-b", "g-1")).toEqual(["garment", "user-b", "g-1"]);
    expect(queryKeys.garment("user-a", "g-2")).toEqual(["garment", "user-a", "g-2"]);
    expect(queryKeys.garment("user-a", "g-1")).not.toEqual(queryKeys.garment("user-b", "g-1"));
  });

  it("isolates wardrobe query key per user, limit and offset", () => {
    expect(queryKeys.wardrobe("user-a", 20, 0)).toEqual(["wardrobe", "user-a", 20, 0]);
    expect(queryKeys.wardrobe("user-b", 20, 0)).toEqual(["wardrobe", "user-b", 20, 0]);
    expect(queryKeys.wardrobe("user-a", 50, 20)).toEqual(["wardrobe", "user-a", 50, 20]);
    expect(queryKeys.wardrobe("user-a", 20, 0)).not.toEqual(queryKeys.wardrobe("user-b", 20, 0));
  });

  it("isolates tryOnJobs query key per user and limit", () => {
    expect(queryKeys.tryOnJobs("user-a", 10)).toEqual(["tryon", "jobs", "user-a", 10]);
    expect(queryKeys.tryOnJobs("user-b", 10)).toEqual(["tryon", "jobs", "user-b", 10]);
    expect(queryKeys.tryOnJobs("user-a", 10)).not.toEqual(queryKeys.tryOnJobs("user-b", 10));
  });

  it("isolates tryOnJob query key per user and job ID", () => {
    expect(queryKeys.tryOnJob("user-a", "job-1")).toEqual(["tryon", "job", "user-a", "job-1"]);
    expect(queryKeys.tryOnJob("user-b", "job-1")).toEqual(["tryon", "job", "user-b", "job-1"]);
    expect(queryKeys.tryOnJob("user-a", "job-2")).toEqual(["tryon", "job", "user-a", "job-2"]);
    expect(queryKeys.tryOnJob("user-a", "job-1")).not.toEqual(queryKeys.tryOnJob("user-b", "job-1"));
  });

  it("isolates derivedProfile query key per user ID", () => {
    expect(queryKeys.derivedProfile("user-a")).toEqual(["derivedProfile", "user-a"]);
    expect(queryKeys.derivedProfile("user-b")).toEqual(["derivedProfile", "user-b"]);
    expect(queryKeys.derivedProfile("user-a")).not.toEqual(queryKeys.derivedProfile("user-b"));
  });
});
