import { File } from "expo-file-system";

export async function cleanupFile(uri: string | null | undefined): Promise<boolean> {
  if (!uri) return false;
  try {
    const file = new File(uri);
    file.delete();
    return true;
  } catch {
    try {
      const { deleteAsync } = await import("expo-file-system/legacy");
      await deleteAsync(uri, { idempotent: true });
      return true;
    } catch {
      return false;
    }
  }
}

export async function cleanupFiles(uris: (string | null | undefined)[]): Promise<void> {
  for (const uri of uris) {
    if (uri) {
      await cleanupFile(uri);
    }
  }
}
