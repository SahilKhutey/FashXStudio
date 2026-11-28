export function isSafeMerchantUrl(url: string | null | undefined): boolean {
  if (!url) return false;
  try {
    const parsed = new URL(url.trim());
    return parsed.protocol === "https:";
  } catch {
    return false;
  }
}

export function priceToMinorUnits(amount: string | number): number {
  const parsed = typeof amount === "number" ? amount : Number(amount);
  if (!Number.isFinite(parsed) || parsed < 0) {
    return 0;
  }
  return Math.round(parsed * 100);
}
