export function formatMinorPrice(
  amountMinor: number,
  currency: string,
  locale = "en-IN",
): string {
  if (!Number.isSafeInteger(amountMinor) || amountMinor < 0) {
    return "Price unavailable";
  }

  try {
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency,
      maximumFractionDigits: 2,
    }).format(amountMinor / 100);
  } catch {
    return `${currency} ${(amountMinor / 100).toFixed(2)}`;
  }
}

export function getDiscountPercentage(
  currentMinor: number,
  originalMinor?: number | null,
): number | null {
  if (
    originalMinor == null ||
    originalMinor <= 0 ||
    currentMinor < 0 ||
    currentMinor >= originalMinor
  ) {
    return null;
  }

  return Math.round(((originalMinor - currentMinor) / originalMinor) * 100);
}
