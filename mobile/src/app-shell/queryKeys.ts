export const queryKeys = {
  me: (userId: string | null) => ["me", userId] as const,
  feed: (userId: string | null) => ["feed", userId] as const,
  garment: (userId: string | null, garmentId: string) =>
    ["garment", userId, garmentId] as const,
  wardrobe: (
    userId: string | null,
    limit: number,
    offset: number
  ) => ["wardrobe", userId, limit, offset] as const,
  tryOnJobs: (userId: string | null, limit: number) =>
    ["tryon", "jobs", userId, limit] as const,
  tryOnJob: (userId: string | null, jobId: string | null) =>
    ["tryon", "job", userId, jobId] as const,
  derivedProfile: (userId: string | null) =>
    ["derivedProfile", userId] as const,
};
