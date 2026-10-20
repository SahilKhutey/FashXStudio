const WEEK = 7 * 24 * 3600 * 1000;

export const fitCardDue = (
  i: { purchased_at?: string | null; fit_feedback_given?: boolean },
  now = Date.now()
): boolean =>
  !!i.purchased_at &&
  !i.fit_feedback_given &&
  now - new Date(i.purchased_at).getTime() >= WEEK;

export const priceNote = (i: {
  price_at_save: number;
  current_price?: number | null;
}): { saved: number; now: number } | null =>
  i.current_price != null && i.current_price !== i.price_at_save
    ? { saved: i.price_at_save, now: i.current_price }
    : null; // never rewrite the snapshot
