import { fitCardDue, priceNote } from "../src/features/wardrobe/logic";

describe("Slice 3 Wardrobe Logic: fitCardDue", () => {
  const ONE_DAY = 24 * 3600 * 1000;
  const SEVEN_DAYS = 7 * ONE_DAY;
  const NOW = 1770000000000; // Fixed reference timestamp

  it("is not due when item has never been purchased", () => {
    expect(
      fitCardDue({ purchased_at: null, fit_feedback_given: false }, NOW)
    ).toBe(false);
    expect(
      fitCardDue({ purchased_at: undefined, fit_feedback_given: false }, NOW)
    ).toBe(false);
  });

  it("is not due when purchased 6 days ago (< 7 days)", () => {
    const purchasedAt = new Date(NOW - 6 * ONE_DAY).toISOString();
    expect(
      fitCardDue({ purchased_at: purchasedAt, fit_feedback_given: false }, NOW)
    ).toBe(false);
  });

  it("is due exactly at 7 days after purchase", () => {
    const purchasedAt = new Date(NOW - SEVEN_DAYS).toISOString();
    expect(
      fitCardDue({ purchased_at: purchasedAt, fit_feedback_given: false }, NOW)
    ).toBe(true);
  });

  it("is due when purchased more than 7 days ago (e.g. 10 days)", () => {
    const purchasedAt = new Date(NOW - 10 * ONE_DAY).toISOString();
    expect(
      fitCardDue({ purchased_at: purchasedAt, fit_feedback_given: false }, NOW)
    ).toBe(true);
  });

  it("is not due when fit feedback has already been given, even after 7 days", () => {
    const purchasedAt = new Date(NOW - 10 * ONE_DAY).toISOString();
    expect(
      fitCardDue({ purchased_at: purchasedAt, fit_feedback_given: true }, NOW)
    ).toBe(false);
  });
});

describe("Slice 3 Wardrobe Logic: priceNote", () => {
  it("returns null when current_price equals price_at_save", () => {
    const item = { price_at_save: 299900, current_price: 299900 };
    expect(priceNote(item)).toBeNull();
  });

  it("returns null when current_price is null (garment gone or unlisted)", () => {
    const item = { price_at_save: 299900, current_price: null };
    expect(priceNote(item)).toBeNull();
  });

  it("returns null when current_price is undefined", () => {
    const item = { price_at_save: 299900, current_price: undefined };
    expect(priceNote(item)).toBeNull();
  });

  it("returns { saved, now } when current_price differs from price_at_save", () => {
    const item = { price_at_save: 299900, current_price: 249900 };
    const note = priceNote(item);
    expect(note).toEqual({ saved: 299900, now: 249900 });
  });

  it("never mutates the original snapshot item", () => {
    const original = Object.freeze({ price_at_save: 399900, current_price: 449900 });
    const note = priceNote(original);
    expect(note).toEqual({ saved: 399900, now: 449900 });
    expect(original.price_at_save).toBe(399900);
  });
});
