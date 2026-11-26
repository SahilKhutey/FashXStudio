import React from "react";
import { fireEvent, render } from "@testing-library/react-native";

import { fitProfileApi } from "../src/features/fit-profile/api/fitProfileApi";
import { FitPreferenceSelector } from "../src/features/fit-profile/components/FitPreferenceSelector";
import { MeasurementGuidanceCard } from "../src/features/fit-profile/components/MeasurementGuidanceCard";
import { MeasurementInput } from "../src/features/fit-profile/components/MeasurementInput";
import { useFitProfileStore } from "../src/features/fit-profile/store/fitProfileStore";
import type { MeasurementDefinition, ShopperFitProfile } from "../src/features/fit-profile/types";

jest.mock("../src/api/client", () => ({
  api: jest.fn(),
}));

describe("Phase 08.2 Mobile: Shopper Fit Profile", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useFitProfileStore.getState().clearProfile();
  });

  describe("fitProfileApi", () => {
    it("calls authenticated /profile/fit endpoints for measurements and preferences", async () => {
      const { api } = require("../src/api/client");
      (api as jest.Mock).mockResolvedValue({ status: "PROFILE_INCOMPLETE" });

      await fitProfileApi.getProfile();
      expect(api).toHaveBeenCalledWith("/profile/fit");

      await fitProfileApi.addMeasurements([
        { field: "CHEST", value: "38", unit: "IN" },
      ]);
      expect(api).toHaveBeenCalledWith(
        "/profile/fit/measurements",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            measurements: [{ field: "CHEST", value: "38", unit: "IN" }],
          }),
        }),
      );

      await fitProfileApi.updateCategoryPreference("TSHIRTS", "RELAXED");
      expect(api).toHaveBeenCalledWith(
        "/profile/fit/preferences/TSHIRTS",
        expect.objectContaining({
          method: "PUT",
          body: JSON.stringify({ fit_preference: "RELAXED" }),
        }),
      );
    });
  });

  describe("useFitProfileStore", () => {
    it("clears profile state cleanly on logout/consent withdrawal", () => {
      const sampleProfile: ShopperFitProfile = {
        status: "PROFILE_READY",
        profile_id: "prof-1",
        schema_version: "1.0",
        preferred_unit: "CM",
        default_fit_preference: "REGULAR",
        measurements: [],
        category_preferences: [],
        category_readiness: {},
        consents: { fit_profile_storage: true },
        version: 1,
      };
      useFitProfileStore.getState().setProfile(sampleProfile);
      expect(useFitProfileStore.getState().profile).not.toBeNull();

      useFitProfileStore.getState().clearProfile();
      expect(useFitProfileStore.getState().profile).toBeNull();
      expect(useFitProfileStore.getState().history).toEqual([]);
    });
  });

  describe("MeasurementGuidanceCard component", () => {
    const chestDef: MeasurementDefinition = {
      code: "CHEST",
      display_name: "Chest",
      explanation: "Measure around the fullest part of your chest. Keep the tape level.",
      tape_positioning: "Wrap horizontally under arms.",
      how_to_hold: "Hold relaxed.",
      example_input: "96.5 cm or 38.0 in",
      measurement_type: "CIRCUMFERENCE",
      supported_categories: ["TSHIRTS", "SHIRTS"],
      default_unit: "CM",
      is_optional_contextual: false,
    };

    it("renders guidance explanation, tape position, and example format", async () => {
      const { getByText } = await render(<MeasurementGuidanceCard definition={chestDef} />);
      expect(getByText("How to measure: Chest")).toBeTruthy();
      expect(getByText(/fullest part of your chest/)).toBeTruthy();
      expect(getByText(/Wrap horizontally under arms/)).toBeTruthy();
      expect(getByText(/96.5 cm or 38.0 in/)).toBeTruthy();
    });
  });

  describe("MeasurementInput component", () => {
    it("validates invalid values, previews CM conversion for inches, and submits", async () => {
      const onSave = jest.fn().mockResolvedValue(undefined);
      const { getByLabelText, getByText } = await render(
        <MeasurementInput
          title="Chest"
          explanation="Measure around chest."
          fieldCode="CHEST"
          onSave={onSave}
        />,
      );

      // Zero / invalid entry rejected inline without calling onSave
      await fireEvent.changeText(getByLabelText("Chest measurement"), "0");
      await fireEvent.press(getByText("Save measurement"));
      expect(getByText("Enter a valid positive measurement.")).toBeTruthy();
      expect(onSave).not.toHaveBeenCalled();

      // Switch unit to IN and enter 38 -> preview 96.52 CM
      await fireEvent.press(getByLabelText("Unit IN"));
      await fireEvent.changeText(getByLabelText("Chest measurement"), "38");
      expect(getByText("Normalized preview: 96.52 CM")).toBeTruthy();

      await fireEvent.press(getByText("Save measurement"));
      expect(onSave).toHaveBeenCalledWith("38", "IN", false);
    });

    it("asks confirmation before replacing an existing saved measurement", async () => {
      const onSave = jest.fn().mockResolvedValue(undefined);
      const { getByText } = await render(
        <MeasurementInput
          title="Waist"
          explanation="Measure around waist."
          fieldCode="WAIST"
          initialValue="80"
          hasExistingValue={true}
          onSave={onSave}
        />,
      );

      await fireEvent.press(getByText("Save measurement"));
      expect(onSave).not.toHaveBeenCalled();
      expect(getByText(/Press Save again to confirm replacing/)).toBeTruthy();

      await fireEvent.press(getByText("Confirm update"));
      expect(onSave).toHaveBeenCalledWith("80", "CM", false);
    });
  });

  describe("FitPreferenceSelector component", () => {
    it("renders subjective fit preferences with non-equivalence disclaimer", async () => {
      const onSelect = jest.fn();
      const { getByLabelText, getByText } = await render(
        <FitPreferenceSelector
          title="T-shirts fit"
          selected="REGULAR"
          onSelect={onSelect}
        />,
      );

      expect(getByText(/not physical-fit verification or a universal brand size/)).toBeTruthy();
      await fireEvent.press(getByLabelText("T-shirts fit: Relaxed"));
      expect(onSelect).toHaveBeenCalledWith("RELAXED");
    });
  });
});
