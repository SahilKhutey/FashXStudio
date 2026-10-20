import { z } from "zod";

export const step1Schema = z.object({
  gender: z.enum(["female", "male", "unisex"]),
  topSize: z.string().min(1, "Top size is required"),
  bottomSize: z.string().min(1, "Bottom size is required"),
});

export const step2Schema = z.object({
  heightCm: z
    .number({ message: "Height must be a number" })
    .int("Height must be a whole number")
    .min(120, "Height must be at least 120 cm")
    .max(230, "Height must be under 230 cm"),
  weightKg: z
    .number()
    .min(30)
    .max(250)
    .optional(),
  build: z.enum(["slim", "athletic", "regular", "broad"]).optional(),
});

export const step3Schema = z
  .object({
    budgetMin: z
      .number({ message: "Minimum budget must be a number" })
      .int("Budget must be a whole number")
      .min(0, "Minimum budget cannot be negative"),
    budgetMax: z
      .number({ message: "Maximum budget must be a number" })
      .int("Budget must be a whole number")
      .min(0, "Maximum budget cannot be negative"),
    occasions: z
      .array(z.string())
      .min(1, "Select at least one occasion"),
  })
  .refine((data) => data.budgetMin <= data.budgetMax, {
    message: "Minimum budget cannot exceed maximum budget",
    path: ["budgetMin"],
  });

export type Step1Values = z.infer<typeof step1Schema>;
export type Step2Values = z.infer<typeof step2Schema>;
export type Step3Values = z.infer<typeof step3Schema>;

export const onboardingProfileSchema = z.object({
  gender: z.enum(["female", "male", "unisex"]),
  topSize: z.string().min(1),
  bottomSize: z.string().min(1),
  heightCm: z.number().int().min(120).max(230),
  budgetMin: z.number().int().min(0),
  budgetMax: z.number().int().min(0),
  occasions: z.array(z.string()).min(1),
});
