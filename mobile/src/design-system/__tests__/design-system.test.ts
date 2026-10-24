import { resolveTheme } from "../theme";
import {
  getScreenGutter,
  getScreenSize,
  getProductGridColumns,
  getContentWidth,
} from "../tokens/responsive";

describe("theme resolution", () => {
  it("uses the light theme for light mode", () => {
    expect(resolveTheme("light", "dark").mode).toBe("light");
  });

  it("uses the dark theme for dark mode", () => {
    expect(resolveTheme("dark", "light").mode).toBe("dark");
  });

  it("follows the system theme when mode is system", () => {
    expect(resolveTheme("system", "dark").mode).toBe("dark");
    expect(resolveTheme("system", "light").mode).toBe("light");
  });

  it("defaults to light when the system scheme is unavailable", () => {
    expect(resolveTheme("system", null).mode).toBe("light");
  });
});

describe("responsive tokens", () => {
  it("classifies compact and tablet screens", () => {
    expect(getScreenSize(320)).toBe("compact");
    expect(getScreenSize(600)).toBe("phone");
    expect(getScreenSize(800)).toBe("tablet");
    expect(getScreenSize(1200)).toBe("desktop");
  });

  it("returns a larger gutter for wider screens", () => {
    expect(getScreenGutter(320)).toBe(12);
    expect(getScreenGutter(390)).toBe(16);
    expect(getScreenGutter(800)).toBe(24);
    expect(getScreenGutter(1200)).toBe(32);
  });

  it("increases product grid columns on wider screens", () => {
    expect(getProductGridColumns(320)).toBe(1);
    expect(getProductGridColumns(390)).toBe(2);
    expect(getProductGridColumns(800)).toBe(3);
    expect(getProductGridColumns(1200)).toBe(4);
  });

  it("does not exceed the maximum content width", () => {
    expect(getContentWidth(390, 720)).toBe(390);
    expect(getContentWidth(1200, 720)).toBe(720);
  });
});
