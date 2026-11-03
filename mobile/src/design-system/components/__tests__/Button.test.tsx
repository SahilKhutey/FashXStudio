import React from "react";
import { fireEvent, render } from "@testing-library/react-native";
import { Button } from "../Button";

jest.mock("../AppText", () => ({
  AppText: ({ children }: { children: React.ReactNode }) => {
    const { Text } = require("react-native");
    return <Text>{children}</Text>;
  },
}));

jest.mock("../../useDesignTokens", () => ({
  useDesignTokens: () => ({
    colors: {
      brand: "#7069E8",
      surfaceSecondary: "#EEEEEE",
      textOnBrand: "#FFFFFF",
      textPrimary: "#171717",
      danger: "#DC4545",
      borderStrong: "#777777",
    },
    spacing: { 3: 12, 4: 16 },
    radius: { md: 12 },
  }),
}));

describe("Button", () => {
  it("renders the provided title", async () => {
    const { getByText } = await render(
      <Button title="Save" onPress={() => {}} />
    );
    expect(getByText("Save")).toBeTruthy();
  });

  it("calls onPress", async () => {
    const onPress = jest.fn();
    const { getByRole } = await render(
      <Button title="Save" onPress={onPress} />
    );
    fireEvent.press(getByRole("button"));
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it("does not execute when disabled", async () => {
    const onPress = jest.fn();
    const { getByRole } = await render(
      <Button title="Save" onPress={onPress} disabled />
    );
    fireEvent.press(getByRole("button"));
    expect(onPress).not.toHaveBeenCalled();
  });

  it("disables the action during loading", async () => {
    const onPress = jest.fn();
    const { getByRole } = await render(
      <Button title="Save" onPress={onPress} loading />
    );
    expect(getByRole("button").props.accessibilityState.busy).toBe(true);
    fireEvent.press(getByRole("button"));
    expect(onPress).not.toHaveBeenCalled();
  });
});
