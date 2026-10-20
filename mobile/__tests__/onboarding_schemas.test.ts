import {
  step1Schema,
  step2Schema,
  step3Schema,
  onboardingProfileSchema,
} from "../src/features/onboarding/schemas";

describe("Onboarding Form Schemas (Zod)", () => {
  describe("Step 1: Gender and Sizing", () => {
    it("accepts valid step 1 inputs", () => {
      const res = step1Schema.safeParse({
        gender: "female",
        topSize: "M",
        bottomSize: "S",
      });
      expect(res.success).toBe(true);
    });

    it("rejects invalid gender or missing sizes", () => {
      const invalidGender = step1Schema.safeParse({
        gender: "other",
        topSize: "M",
        bottomSize: "S",
      });
      expect(invalidGender.success).toBe(false);

      const emptySize = step1Schema.safeParse({
        gender: "male",
        topSize: "",
        bottomSize: "L",
      });
      expect(emptySize.success).toBe(false);
    });
  });

  describe("Step 2: Body Measurements", () => {
    it("accepts valid height and optional measurements", () => {
      const res = step2Schema.safeParse({
        heightCm: 172,
        weightKg: 68,
        build: "athletic",
      });
      expect(res.success).toBe(true);
    });

    it("rejects height below 120 cm", () => {
      const res = step2Schema.safeParse({
        heightCm: 119,
      });
      expect(res.success).toBe(false);
      if (!res.success) {
        expect(res.error.issues[0]?.message).toMatch(/at least 120/i);
      }
    });

    it("rejects height above 230 cm", () => {
      const res = step2Schema.safeParse({
        heightCm: 231,
      });
      expect(res.success).toBe(false);
    });

    it("rejects non-integer height", () => {
      const res = step2Schema.safeParse({
        heightCm: 172.5,
      });
      expect(res.success).toBe(false);
    });

    it("rejects weight outside 30-250 range", () => {
      expect(step2Schema.safeParse({ heightCm: 170, weightKg: 20 }).success).toBe(false);
      expect(step2Schema.safeParse({ heightCm: 170, weightKg: 300 }).success).toBe(false);
    });
  });

  describe("Step 3: Budget and Occasions", () => {
    it("accepts valid budget range and occasions", () => {
      const res = step3Schema.safeParse({
        budgetMin: 50,
        budgetMax: 200,
        occasions: ["casual", "work"],
      });
      expect(res.success).toBe(true);
    });

    it("rejects budgetMin > budgetMax", () => {
      const res = step3Schema.safeParse({
        budgetMin: 300,
        budgetMax: 100,
        occasions: ["party"],
      });
      expect(res.success).toBe(false);
      if (!res.success) {
        expect(res.error.issues[0]?.message).toMatch(/cannot exceed maximum/i);
      }
    });

    it("rejects negative budgets", () => {
      const res = step3Schema.safeParse({
        budgetMin: -10,
        budgetMax: 100,
        occasions: ["party"],
      });
      expect(res.success).toBe(false);
    });

    it("rejects empty occasions list", () => {
      const res = step3Schema.safeParse({
        budgetMin: 50,
        budgetMax: 200,
        occasions: [],
      });
      expect(res.success).toBe(false);
      if (!res.success) {
        expect(res.error.issues[0]?.message).toMatch(/at least one occasion/i);
      }
    });
  });

  describe("Combined Onboarding Profile Schema", () => {
    it("validates full profile payload", () => {
      const valid = onboardingProfileSchema.safeParse({
        gender: "unisex",
        topSize: "L",
        bottomSize: "L",
        heightCm: 180,
        budgetMin: 20,
        budgetMax: 150,
        occasions: ["casual"],
      });
      expect(valid.success).toBe(true);
    });
  });
});
