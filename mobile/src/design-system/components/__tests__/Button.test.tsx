import React from "react";
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
  it("renders the provided title and default button accessibility props", () => {
    const onPress = jest.fn();
    const element = Button({ title: "Save", onPress });
    expect(element.props.accessibilityRole).toBe("button");
    expect(element.props.accessibilityLabel).toBe("Save");
    expect(element.props.disabled).toBe(false);
    expect(element.props.accessibilityState).toEqual({ disabled: false, busy: false });
  });

  it("calls onPress when invoked", () => {
    const onPress = jest.fn();
    const element = Button({ title: "Save", onPress });
    element.props.onPress();
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it("does not execute when disabled", () => {
    const onPress = jest.fn();
    const element = Button({ title: "Save", onPress, disabled: true });
    expect(element.props.disabled).toBe(true);
    expect(element.props.accessibilityState.disabled).toBe(true);
  });

  it("disables the action and flags busy during loading", () => {
    const onPress = jest.fn();
    const element = Button({ title: "Save", onPress, loading: true });
    expect(element.props.disabled).toBe(true);
    expect(element.props.accessibilityState.busy).toBe(true);
  });
});
